import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { REDIRECTS, SERVICES } from './site.js'
import ScrollToTop from './lib/ScrollToTop.jsx'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import { MobileCallBar, FloatingWhatsApp } from './components/MobileCallBar.jsx'
import HomePage from './pages/HomePage.jsx'
import ServicePage from './pages/ServicePage.jsx'
import ContactPage from './pages/ContactPage.jsx'
import ServicesPage from './pages/ServicesPage.jsx'
import NotFound from './pages/NotFound.jsx'

function Layout() {
  return (
    <div className="relative">
      <div className="noise-overlay" />
      <ScrollToTop />
      <Navbar />
      <main className="pb-20 lg:pb-0">
        <Outlet />
      </main>
      <Footer />
      <MobileCallBar />
      <FloatingWhatsApp />
    </div>
  )
}

/* Routes exist only for enabled services; disabled ones fall through to 404 even by direct URL. */
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        {SERVICES.length > 0 && <Route path="/servicos" element={<ServicesPage />} />}
        <Route path="/contato" element={<ContactPage />} />
        {SERVICES.map((s) => <Route key={s.id} path={s.href} element={<ServicePage service={s} />} />)}
        {Object.entries(REDIRECTS).map(([from, to]) => <Route key={from} path={from} element={<Navigate to={to} replace />} />)}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
