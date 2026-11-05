import { Footer, Header } from './components/Chrome'
import { Hallazgos } from './components/Hallazgos'
import { Hero } from './components/Hero'
import { Metodo } from './components/Metodo'
import { Radar } from './components/Radar'
import { Validacion } from './components/Validacion'
import { useData } from './lib/data'

export default function App() {
  const { data, error } = useData()
  return (
    <>
      <Header />
      {data ? (
        <main>
          <Hero r={data.resumen} porAnio={data.porAnio} />
          <Radar ranking={data.ranking} corte={data.resumen.corte_ranking} total={data.resumen.moleculas_cum} />
          <Hallazgos r={data.resumen} diagnosticos={data.diagnosticos} />
          <Validacion r={data.resumen} />
          <Metodo />
        </main>
      ) : (
        <main className="grid min-h-svh place-items-center text-dim">{error ?? 'Cargando el radar…'}</main>
      )}
      <Footer />
    </>
  )
}
