import { motion } from 'motion/react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { fmt, pct, type PorAnio, type Resumen } from '../lib/data'

export function Hero({ r, porAnio }: { r: Resumen; porAnio: PorAnio[] }) {
  return (
    <section className="px-5 pt-28 pb-16 md:px-10">
      <div className="mx-auto max-w-6xl">
        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl font-serif text-[clamp(2.6rem,6.5vw,5.4rem)] leading-[0.98] font-semibold tracking-[-0.02em]"
        >
          ¿Qué medicamento va a faltar el próximo año en Colombia?
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="mt-6 max-w-2xl text-lg leading-relaxed text-dim">
          Cuando un medicamento desaparece de las farmacias, el INVIMA autoriza importarlo como <em>vital no disponible</em>. Crucé esas{' '}
          {fmt.format(r.autorizaciones)} autorizaciones con el registro de todos los medicamentos del país y entrené un modelo que anticipa cuáles
          entrarán a la lista en los próximos doce meses.
        </motion.p>

        <div className="mt-12 grid gap-8 md:grid-cols-[1fr_1.4fr] md:items-end">
          <dl className="grid grid-cols-3 gap-4 md:grid-cols-1 md:gap-6">
            <Stat value={fmt.format(r.autorizaciones)} label="importaciones de emergencia desde 2018" />
            <Stat value={fmt.format(r.con_registro)} label="moléculas con registro sanitario que aun así faltaron" />
            <Stat value={pct(r.recurrencia)} label="de los desabastecimientos se repiten" accent />
          </dl>
          <figure>
            <figcaption className="mb-2 text-sm text-dim">Autorizaciones por año · 2026 hasta septiembre</figcaption>
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={porAnio} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
                  <XAxis dataKey="anio" tickLine={false} axisLine={false} fontSize={12} stroke="#8a8a8a" />
                  <Tooltip
                    cursor={{ fill: '#e4e1da', opacity: 0.6 }}
                    content={({ active, payload }) =>
                      active && payload?.[0] ? (
                        <div className="rounded-md bg-ink px-3 py-2 text-sm text-white">
                          <p className="font-semibold">{payload[0].payload.anio}</p>
                          <p>{fmt.format(payload[0].payload.autorizaciones)} autorizaciones</p>
                          <p>{payload[0].payload.moleculas} moléculas distintas</p>
                        </div>
                      ) : null
                    }
                  />
                  <Bar dataKey="autorizaciones" radius={[4, 4, 0, 0]} animationDuration={1200}>
                    {porAnio.map((p) => (
                      <Cell key={p.anio} fill={p.anio >= 2024 ? '#c8102e' : '#d9b3b9'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </figure>
        </div>
      </div>
    </section>
  )
}

function Stat({ value, label, accent }: { value: string; label: string; accent?: boolean }) {
  return (
    <div className="border-t-2 border-ink pt-3">
      <dd className={`font-serif text-4xl font-semibold tracking-tight md:text-5xl ${accent ? 'text-alert' : ''}`}>{value}</dd>
      <dt className="mt-1 text-sm leading-snug text-dim">{label}</dt>
    </div>
  )
}
