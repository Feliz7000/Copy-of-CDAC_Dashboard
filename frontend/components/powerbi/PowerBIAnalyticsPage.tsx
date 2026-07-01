'use client';

import PowerBIReportEmbed from '@/components/powerbi/PowerBIReportEmbed';

export default function PowerBIAnalyticsPage({
  title,
  description,
  studentScoped,
}: {
  title?: string;
  description?: string;
  studentScoped?: boolean;
}) {
  return (
    <div className="flex flex-col gap-6 w-full max-w-[1600px] mx-auto p-4 md:p-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">{title || 'Power BI Analytics'}</h2>
        <p className="text-muted-foreground">
          {description ||
            'Interactive CDAC executive report. Requires Power BI Embedded (or eligible Premium/Pro) capacity configured on the server.'}
        </p>
      </div>
      <PowerBIReportEmbed studentScoped={studentScoped} />
    </div>
  );
}
