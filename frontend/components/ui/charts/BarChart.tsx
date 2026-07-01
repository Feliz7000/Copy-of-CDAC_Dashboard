"use client"

import { Bar, BarChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { m, LazyMotion, domAnimation } from "framer-motion"

interface BarData {
  name: string
  total: number
}

interface AnimatedBarChartProps {
  data: BarData[]
  title?: string
  description?: string
  color?: string
}

export function AnimatedBarChart({ 
  data, 
  title, 
  description,
  color = "hsl(var(--primary))" 
}: AnimatedBarChartProps) {
  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full h-full min-h-[300px] flex flex-col"
      >
        {(title || description) && (
          <div className="mb-4">
            {title && <h4 className="text-lg font-semibold">{title}</h4>}
            {description && <p className="text-sm text-muted-foreground">{description}</p>}
          </div>
        )}
        <div className="w-full">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="name" 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                tickFormatter={(value) => `${value}`} 
              />
              <Tooltip 
                cursor={{ fill: "hsl(var(--accent))", opacity: 0.4 }}
                contentStyle={{ 
                  backgroundColor: "hsl(var(--card))",
                  borderColor: "hsl(var(--border))",
                  borderRadius: "8px",
                  color: "hsl(var(--card-foreground))"
                }}
              />
              <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </m.div>
    </LazyMotion>
  )
}
