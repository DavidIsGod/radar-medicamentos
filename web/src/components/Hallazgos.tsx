import { motion } from 'motion/react'
import { fmt, pct, type Resumen } from '../lib/data'

export function Hallazgos({ r, diagnosticos }: { r: Resumen; diagnosticos: { diagnostico: string; n: number }[] }) {
  const max = diagnosticos[0]?.n ?? 1
  const cards = [
    {
      t: 'El desabastecimiento es crónico',
      d: `${pct(r.recurrencia)} de las moléculas que necesitan importación de emergencia en un año ya habían estado en la lista antes. Lo que falta hoy tiende a seguir faltando.`,
    },
    {
      t: 'Faltan los genéricos esenciales',
      d: 'Contra la intuición, no son los medicamentos raros: las moléculas que entran a la lista tienen en promedio 5 titulares activos, frente a 2,7 del resto. Anestésicos, electrolitos y oncológicos clásicos: alto uso y bajo margen.',
    },
    {
      t: 'Las crisis se contagian por clase',
      d: 'Si otras moléculas del mismo grupo terapéutico (ATC nivel 3) estuvieron en la lista el último año, el riesgo de una molécula se triplica: 3,0 % frente a 0,95 %.',
    },
  ]
  return (
    <section className="px-5 py-20 md:px-10">
      <div className="mx-auto max-w-6xl">
        <h2 className="font-serif text-4xl font-semibold tracking-tight md:text-5xl">Lo que muestran los datos</h2>
        <div className="mt-10 grid gap-8 md:grid-cols-3">
          {cards.map((c, i) => (
            <motion.article
              key={c.t}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
              className="border-t-2 border-ink pt-4"
            >
              <h3 className="font-serif text-2xl font-semibold">{c.t}</h3>
              <p className="mt-2 leading-relaxed text-dim">{c.d}</p>
            </motion.article>
          ))}
        </div>

        <div className="mt-16 grid gap-10 md:grid-cols-[1fr_1.4fr]">
          <div>
            <h3 className="font-serif text-2xl font-semibold">¿Para quién se importa?</h3>
            <p className="mt-2 text-dim">
              Diagnósticos más frecuentes en las {fmt.format(r.autorizaciones)} autorizaciones. Muchas son enfermedades raras: pacientes con pocas
              alternativas cuando el medicamento falta.
            </p>
          </div>
          <ol className="space-y-2">
            {diagnosticos.map((d) => (
              <li key={d.diagnostico} className="grid grid-cols-[1fr_auto] items-center gap-3 text-sm">
                <span>
                  <span className="block truncate">{d.diagnostico}</span>
                  <span className="mt-1 block h-1.5 overflow-hidden rounded-full bg-rule">
                    <motion.span className="block h-full bg-alert" initial={{ width: 0 }} whileInView={{ width: `${(d.n / max) * 100}%` }} viewport={{ once: true }} transition={{ duration: 0.9 }} />
                  </span>
                </span>
                <span className="font-semibold tabular-nums">{fmt.format(d.n)}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  )
}
