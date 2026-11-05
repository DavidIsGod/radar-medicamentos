import { NOTEBOOK_URL, REPO_URL } from '../lib/data'

const PASOS = [
  ['Datos abiertos', 'Tres datasets del INVIMA en datos.gov.co: vitales no disponibles y el CUM vigente y vencido (~320.000 filas).'],
  ['Limpieza', 'Normalización de nombres de moléculas (sales, hidratos, orden de palabras, combinaciones) para cruzar ambas fuentes.'],
  ['Panel temporal', 'Para cada 31 de diciembre se reconstruye el mercado con solo lo conocido hasta esa fecha: nada del futuro se filtra.'],
  ['Modelos', 'Regresión logística y gradient boosting de scikit-learn, combinados en un ensamble de rangos.'],
  ['Validación', 'Origen móvil sobre cuatro años, contra una línea base de persistencia; explicaciones por contribución de variables.'],
]

export function Metodo() {
  return (
    <section className="px-5 py-20 md:px-10">
      <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-[1fr_1.3fr]">
        <div>
          <h2 className="font-serif text-4xl font-semibold tracking-tight md:text-5xl">Cómo está hecho</h2>
          <p className="mt-3 text-dim">Python, pandas y scikit-learn. Todo el análisis, con gráficos y conclusiones, está en el notebook.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a href={NOTEBOOK_URL} target="_blank" rel="noreferrer" className="rounded-full bg-ink px-5 py-2.5 font-medium text-white transition-colors hover:bg-alert">
              Ver el notebook
            </a>
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="rounded-full border border-ink px-5 py-2.5 font-medium transition-colors hover:border-alert hover:text-alert">
              Código en GitHub
            </a>
          </div>
          <div className="mt-10 rounded-lg bg-amber-soft p-4 text-sm leading-relaxed text-amber">
            <strong>Limitaciones.</strong> La lista de vitales no disponibles mide importaciones autorizadas, no todo el desabastecimiento. El CUM no
            incluye volúmenes de venta. Con ~15 casos nuevos por año, la precisión para moléculas sin historial es baja: el radar sirve para priorizar
            vigilancia, no para tomar decisiones clínicas.
          </div>
        </div>
        <ol className="space-y-6">
          {PASOS.map(([t, d], i) => (
            <li key={t} className="grid grid-cols-[2.5rem_1fr] gap-3">
              <span className="font-serif text-3xl font-semibold text-alert tabular-nums">{i + 1}</span>
              <span>
                <span className="block font-semibold">{t}</span>
                <span className="text-dim">{d}</span>
              </span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
