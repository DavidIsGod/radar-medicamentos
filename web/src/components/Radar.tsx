import { AnimatePresence, motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { ATC, fmt, pct, type Ranking } from '../lib/data'

type Tab = 'todos' | 'nuevos'

export function Radar({ ranking, corte, total }: { ranking: Ranking[]; corte: string; total: number }) {
  const [tab, setTab] = useState<Tab>('todos')
  const [q, setQ] = useState('')
  const [open, setOpen] = useState<string | null>(null)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return ranking
      .map((r, i) => ({ ...r, puesto: i + 1 }))
      .filter((r) => (tab === 'nuevos' ? r.nuevo : true))
      .filter((r) => !needle || r.molecula.toLowerCase().includes(needle) || (ATC[r.atc?.[0]] ?? '').toLowerCase().includes(needle))
      .slice(0, 40)
  }, [ranking, tab, q])

  return (
    <section id="radar" className="scroll-mt-16 border-t border-rule bg-card px-5 py-20 md:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <h2 className="font-serif text-4xl font-semibold tracking-tight md:text-5xl">El radar</h2>
            <p className="mt-3 max-w-2xl text-dim">
              Moléculas ordenadas por riesgo de necesitar importación de emergencia entre octubre de 2026 y septiembre de 2027, con datos hasta el{' '}
              {new Date(corte + 'T12:00').toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })}. Toca una fila para ver
              por qué.
            </p>
          </div>
          <div className="flex rounded-full bg-paper p-1 text-sm" role="tablist">
            {(
              [
                ['todos', 'Mayor riesgo'],
                ['nuevos', 'Candidatos nuevos'],
              ] as [Tab, string][]
            ).map(([k, l]) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === k}
                onClick={() => setTab(k)}
                className={`relative rounded-full px-4 py-2 font-medium transition-colors ${tab === k ? 'text-white' : 'text-dim hover:text-ink'}`}
              >
                {tab === k && <motion.span layoutId="tab" className="absolute inset-0 rounded-full bg-ink" transition={{ type: 'spring', stiffness: 400, damping: 32 }} />}
                <span className="relative">{l}</span>
              </button>
            ))}
          </div>
        </div>

        {tab === 'nuevos' && (
          <p className="mt-6 rounded-lg bg-amber-soft px-4 py-3 text-sm text-amber">
            Moléculas que <strong>nunca</strong> han estado en la lista. Aquí la línea base de persistencia no ve nada: es donde el modelo aporta
            señal propia (y donde más incertidumbre hay).
          </p>
        )}

        <label className="mt-8 block">
          <span className="sr-only">Buscar medicamento</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar: metotrexato, oncología, sistema nervioso…"
            className="w-full rounded-lg border border-rule bg-paper px-4 py-3 outline-none placeholder:text-faint focus:border-ink"
          />
        </label>

        <ol className="mt-4 divide-y divide-rule border-y border-rule">
          {rows.map((r) => {
            const expanded = open === r.molecula
            return (
              <li key={r.molecula}>
                <button onClick={() => setOpen(expanded ? null : r.molecula)} aria-expanded={expanded} className="grid w-full grid-cols-[2.5rem_1fr_auto] items-center gap-4 py-4 text-left md:grid-cols-[3rem_1.2fr_1fr_8rem]">
                  <span className="font-serif text-xl text-faint tabular-nums">{r.puesto}</span>
                  <span>
                    <span className="block text-lg font-semibold">{r.molecula}</span>
                    <span className="text-sm text-dim">
                      {ATC[r.atc?.[0]] ?? 'Sin ATC'} · {r.atc} · vía {r.via}
                    </span>
                  </span>
                  <span className="hidden flex-wrap gap-1.5 md:flex">
                    {r.razones.slice(0, 2).map((z) => (
                      <span key={z} className="rounded-full bg-paper px-2.5 py-1 text-xs text-dim">
                        {z}
                      </span>
                    ))}
                  </span>
                  <RiskBar value={r.riesgo} />
                </button>
                <AnimatePresence initial={false}>
                  {expanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <Detail r={r} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
            )
          })}
          {rows.length === 0 && <li className="py-10 text-center text-dim">Ningún medicamento coincide con la búsqueda.</li>}
        </ol>
        <p className="mt-4 text-sm text-faint">
          El índice es el percentil de riesgo dentro de {fmt.format(total)} moléculas con registro. No es una probabilidad: sirve para priorizar
          vigilancia.
        </p>
      </div>
    </section>
  )
}

function RiskBar({ value }: { value: number }) {
  return (
    <span className="flex items-center justify-end gap-2">
      <span className="hidden h-2 w-16 overflow-hidden rounded-full bg-rule sm:block">
        <motion.span className="block h-full rounded-full bg-alert" initial={{ width: 0 }} whileInView={{ width: `${value * 100}%` }} viewport={{ once: true }} transition={{ duration: 0.8 }} />
      </span>
      <span className="w-12 text-right font-semibold tabular-nums">{(value * 100).toFixed(1).replace('.', ',')}</span>
    </span>
  )
}

function Detail({ r }: { r: Ranking & { puesto: number } }) {
  const items = [
    ['Presentaciones con registro activo', fmt.format(r.presentaciones)],
    ['Titulares activos', fmt.format(r.titulares)],
    ['Presentaciones importadas', pct(r.importadas)],
    ['Autorizaciones de emergencia (último año)', fmt.format(r.vitales_12m)],
    ['Autorizaciones de emergencia (desde 2018)', fmt.format(r.vitales_historico)],
    ['Última autorización', r.ultimo_vital ?? 'Nunca'],
  ]
  return (
    <div className="grid gap-6 pb-6 pl-[3.5rem] md:grid-cols-2 md:pl-[4rem]">
      <div>
        <p className="text-sm font-semibold">Por qué el modelo lo pone aquí</p>
        <ul className="mt-2 space-y-1.5">
          {r.razones.length ? (
            r.razones.map((z) => (
              <li key={z} className="flex items-start gap-2">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-alert" />
                {z}
              </li>
            ))
          ) : (
            <li className="text-dim">Sin una señal individual dominante: el riesgo viene de la combinación de variables.</li>
          )}
        </ul>
      </div>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        {items.map(([k, v]) => (
          <div key={k}>
            <dt className="text-dim">{k}</dt>
            <dd className="text-base font-semibold tabular-nums">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
