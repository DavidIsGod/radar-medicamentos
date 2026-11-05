import { motion, useScroll, useSpring } from 'motion/react'
import { NOTEBOOK_URL, PORTFOLIO_URL, REPO_URL } from '../lib/data'

export function Header() {
  const { scrollYProgress } = useScroll()
  const x = useSpring(scrollYProgress, { stiffness: 120, damping: 30 })
  return (
    <header className="fixed inset-x-0 top-0 z-40 bg-paper/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3 md:px-10">
        <a href={PORTFOLIO_URL} className="text-sm text-dim hover:text-ink">
          ← David Troya
        </a>
        <nav className="flex items-center gap-5 text-sm">
          <a href="#radar" className="hidden hover:text-alert sm:inline">
            Radar
          </a>
          <a href="#validacion" className="hidden hover:text-alert sm:inline">
            Validación
          </a>
          <a href={NOTEBOOK_URL} target="_blank" rel="noreferrer" className="hover:text-alert">
            Notebook ↗
          </a>
        </nav>
      </div>
      <motion.div style={{ scaleX: x }} className="h-0.5 origin-left bg-alert" />
    </header>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-rule px-5 py-12 md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col justify-between gap-3 text-sm text-dim md:flex-row">
        <p>Datos: INVIMA vía datos.gov.co · Análisis independiente, no oficial.</p>
        <p>
          Hecho por{' '}
          <a href={PORTFOLIO_URL} className="text-ink underline-offset-4 hover:underline">
            David Troya
          </a>{' '}
          ·{' '}
          <a href={REPO_URL} className="text-ink underline-offset-4 hover:underline">
            código
          </a>
        </p>
      </div>
    </footer>
  )
}
