import { useEffect, useState } from 'react'

export type Ranking = {
  molecula: string
  atc: string
  via: string
  riesgo: number
  prob: number
  nuevo: boolean
  presentaciones: number
  titulares: number
  importadas: number
  vitales_12m: number
  vitales_historico: number
  ultimo_vital: string | null
  razones: string[]
}
type Fold = Record<string, { roc_auc: number; average_precision: number; precision_at_20: number; recall_at_100: number; auc_casos_nuevos: number }>
export type Resumen = {
  autorizaciones: number
  moleculas_lista: number
  moleculas_cum: number
  con_registro: number
  recurrencia: number
  corte_ranking: string
  metricas: {
    mejor_modelo: string
    validacion_movil: { pliegues: Record<string, Fold>; promedio: Fold }
    pr_modelo: { recall: number; precision: number }[]
    pr_linea_base: { recall: number; precision: number }[]
    importancia: { variable: string; importancia: number }[]
  }
}
export type PorAnio = { anio: number; autorizaciones: number; moleculas: number } & Record<string, number>
export type Data = { resumen: Resumen; porAnio: PorAnio[]; diagnosticos: { diagnostico: string; n: number }[]; ranking: Ranking[] }

export function useData() {
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    const base = `${import.meta.env.BASE_URL}data/`
    const get = (f: string) => fetch(base + f).then((r) => (r.ok ? r.json() : Promise.reject(new Error(f))))
    Promise.all([get('resumen.json'), get('por_anio.json'), get('diagnosticos.json'), get('ranking.json')])
      .then(([resumen, porAnio, diagnosticos, ranking]) => setData({ resumen, porAnio, diagnosticos, ranking }))
      .catch((e: Error) => setError(`No se pudo cargar ${e.message}`))
  }, [])
  return { data, error }
}

export const fmt = new Intl.NumberFormat('es-CO')
export const pct = (v: number, d = 0) => `${(v * 100).toFixed(d).replace('.', ',')} %`
export const dec = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
export const PORTFOLIO_URL = import.meta.env.VITE_PORTFOLIO_URL ?? 'https://davidtroya.vercel.app'
export const REPO_URL = 'https://github.com/DavidIsGod/radar-medicamentos'
export const NOTEBOOK_URL = `${REPO_URL}/blob/main/notebooks/analisis.ipynb`

export const ATC: Record<string, string> = {
  A: 'Digestivo y metabolismo', B: 'Sangre', C: 'Cardiovascular', D: 'Dermatológicos', G: 'Genitourinario', H: 'Hormonas sistémicas',
  J: 'Antiinfecciosos', L: 'Oncología e inmunología', M: 'Musculoesquelético', N: 'Sistema nervioso', P: 'Antiparasitarios',
  R: 'Respiratorio', S: 'Órganos de los sentidos', V: 'Varios',
}
