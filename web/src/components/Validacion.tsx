import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dec, type Resumen } from '../lib/data'

const NAMES: Record<string, string> = {
  linea_base_persistencia: 'Línea base (persistencia)',
  regresion_logistica: 'Regresión logística',
  gradient_boosting: 'Gradient boosting',
  ensamble: 'Ensamble (modelo final)',
}

export function Validacion({ r }: { r: Resumen }) {
  const v = r.metricas.validacion_movil
  const serie = Object.entries(v.pliegues).map(([anio, f]) => ({ anio, base: f.linea_base_persistencia.roc_auc, modelo: f.ensamble.roc_auc }))
  const rows = Object.entries(v.promedio)

  return (
    <section id="validacion" className="scroll-mt-16 border-t border-rule bg-card px-5 py-20 md:px-10">
      <div className="mx-auto max-w-6xl">
        <h2 className="font-serif text-4xl font-semibold tracking-tight md:text-5xl">¿Funciona?</h2>
        <p className="mt-3 max-w-3xl text-dim">
          Validación de origen móvil: para predecir cada año el modelo solo vio los años anteriores. La comparación importante es contra una línea
          base simple, «lo que estuvo en la lista vuelve a estar», que ya es muy buena porque el problema es crónico.
        </p>

        <div className="mt-10 grid gap-10 lg:grid-cols-[1.2fr_1fr]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-dim">
                <tr className="border-b border-ink">
                  <th className="py-2 pr-3 font-medium">Modelo · promedio de 4 años</th>
                  <th className="py-2 pr-3 text-right font-medium">ROC-AUC</th>
                  <th className="py-2 pr-3 text-right font-medium">Recall top 100</th>
                  <th className="py-2 text-right font-medium">AUC casos nuevos</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(([k, m]) => (
                  <tr key={k} className={`border-b border-rule ${k === 'ensamble' ? 'font-semibold text-alert' : ''}`}>
                    <td className="py-3 pr-3">{NAMES[k] ?? k}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{dec(m.roc_auc, 3)}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{dec(m.recall_at_100, 3)}</td>
                    <td className="py-3 text-right tabular-nums">{dec(m.auc_casos_nuevos, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 text-sm leading-relaxed text-dim">
              <strong className="text-ink">Lectura honesta:</strong> en el top 20 la persistencia es casi imbatible. El modelo gana ordenando la lista
              completa y, sobre todo, en los <em>casos nuevos</em>, donde la línea base no distingue nada (AUC 0,5) y el modelo llega a{' '}
              {dec(v.promedio.ensamble.auc_casos_nuevos, 2)}.
            </p>
          </div>
          <figure>
            <figcaption className="mb-2 text-sm text-dim">ROC-AUC por año predicho</figcaption>
            <div className="h-64">
              <ResponsiveContainer>
                <LineChart data={serie} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#e4e1da" />
                  <XAxis dataKey="anio" tickLine={false} axisLine={false} fontSize={12} stroke="#8a8a8a" />
                  <YAxis domain={[0.85, 1]} tickFormatter={(x: number) => dec(x, 2)} tickLine={false} axisLine={false} fontSize={12} stroke="#8a8a8a" width={44} />
                  <Tooltip formatter={(x) => dec(Number(x), 3)} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                  <Line dataKey="base" name="Línea base" stroke="#8a8a8a" strokeWidth={2} dot={{ r: 4 }} />
                  <Line dataKey="modelo" name="Ensamble" stroke="#c8102e" strokeWidth={2.5} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </figure>
        </div>
      </div>
    </section>
  )
}
