'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, BarChart3, ExternalLink } from 'lucide-react';
import { models } from 'powerbi-client';
import type { IReportEmbedConfiguration, Report } from 'powerbi-client';

import { getPowerBIEmbedConfig } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const PowerBIEmbed = dynamic(
  () => import('powerbi-client-react').then((mod) => mod.PowerBIEmbed),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    ),
  },
);

type EmbedPayload = {
  success: boolean;
  configured?: boolean;
  message?: string;
  embed_token?: string;
  embed_url?: string;
  report_id?: string;
  expiration?: string;
  page_name?: string | null;
  hide_page_navigation?: boolean;
  student_scoped?: boolean;
};

const SETUP_VARS = [
  'POWERBI_CLIENT_ID',
  'POWERBI_TENANT_ID',
  'POWERBI_CLIENT_SECRET',
  'POWERBI_WORKSPACE_ID',
  'POWERBI_REPORT_ID',
];

function SetupPanel({ message, configured }: { message: string; configured?: boolean }) {
  return (
    <Card className="border-dashed border-amber-500/30 bg-card/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="h-5 w-5 text-amber-500" />
          Power BI embedding not available
        </CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-muted-foreground">
        <p>
          In-app embedding requires a Power BI <strong>Embedded</strong> capacity (or Premium /
          Pro workspace with embed-for-your-customers). Without that subscription you can still open
          the report in Power BI Desktop or Power BI Service.
        </p>
        {configured ? (
          <p>
            Credentials are present but token generation failed. Check that the Azure AD app is
            enabled for Power BI service principals and has access to the target workspace.
          </p>
        ) : (
          <div>
            <p className="mb-2 font-medium text-foreground">Backend environment variables:</p>
            <ul className="list-disc space-y-1 pl-5 font-mono text-xs">
              {SETUP_VARS.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
            <p className="mt-3">
              Set <code className="text-xs">POWERBI_ENABLE_RLS=true</code> when the dataset defines
              RLS roles (Admin, Hod, Faculty, Student). Students always receive an RLS embed token
              keyed on their PRN.
            </p>
          </div>
        )}
        <Button variant="outline" size="sm" asChild>
          <a
            href="https://learn.microsoft.com/power-bi/developer/embedded/embed-sample-for-customers"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Microsoft embed setup guide
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}

export default function PowerBIReportEmbed({ studentScoped = false }: { studentScoped?: boolean }) {
  const [payload, setPayload] = useState<EmbedPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [embedConfig, setEmbedConfig] = useState<IReportEmbedConfiguration | null>(null);
  const embeddedReportRef = useRef<Report | null>(null);

  const applyStudentView = useCallback(async (report: Report, data: EmbedPayload) => {
    const hideNav = data.hide_page_navigation ?? studentScoped;
    const pageName = data.page_name || (hideNav ? 'Page 2' : null);
    if (hideNav) {
      await report.updateSettings({
        panes: {
          pageNavigation: { visible: false },
          filters: { expanded: false, visible: false },
        },
      });
    }
    if (pageName) {
      const pages = await report.getPages();
      const target = pages.find((p) => p.displayName === pageName || p.name === pageName);
      if (target) {
        await target.setActive();
      }
    }
  }, [studentScoped]);

  const loadConfig = useCallback(async () => {
    const data = await getPowerBIEmbedConfig();
    setPayload(data);
    if (data.success && data.embed_token && data.embed_url && data.report_id) {
      const hideNav = studentScoped || Boolean(data.hide_page_navigation);
      setEmbedConfig({
        type: 'report',
        id: data.report_id,
        embedUrl: data.embed_url,
        accessToken: data.embed_token,
        tokenType: models.TokenType.Embed,
        pageName: data.page_name || (hideNav ? 'Page 2' : undefined),
        settings: {
          panes: {
            filters: { expanded: false, visible: !hideNav },
            pageNavigation: { visible: !hideNav },
          },
          background: models.BackgroundType.Transparent,
        },
      });
    } else {
      setEmbedConfig(null);
    }
    return data;
  }, [studentScoped]);

  useEffect(() => {
    loadConfig()
      .catch((err) => {
        console.error(err);
        setPayload({
          success: false,
          message: 'Could not reach the Power BI configuration endpoint.',
        });
      })
      .finally(() => setLoading(false));
  }, [loadConfig]);

  const handleTokenExpired = useCallback(async () => {
    const refreshed = await loadConfig();
    if (refreshed.success && refreshed.embed_token) {
      embeddedReportRef.current?.setAccessToken(refreshed.embed_token);
    }
  }, [loadConfig]);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!payload?.success || !embedConfig) {
    return (
      <SetupPanel
        message={payload?.message || 'Power BI is not configured for this environment.'}
        configured={payload?.configured}
      />
    );
  }

  return (
    <div className="h-[calc(100vh-10rem)] min-h-[560px] w-full overflow-hidden rounded-lg border bg-background shadow-sm [&_iframe]:h-full [&_iframe]:w-full [&_iframe]:border-0">
      <PowerBIEmbed
        embedConfig={embedConfig}
        cssClassName="h-full w-full"
        eventHandlers={
          new Map([
            ['loaded', async () => {
              const report = embeddedReportRef.current;
              if (report && payload) {
                await applyStudentView(report, payload);
              }
            }],
            ['tokenExpired', handleTokenExpired],
            ['error', (event) => console.error('Power BI embed error', event?.detail)],
          ])
        }
        getEmbeddedComponent={(embeddedReport) => {
          embeddedReportRef.current = embeddedReport;
        }}
      />
    </div>
  );
}
