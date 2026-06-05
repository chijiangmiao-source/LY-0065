import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from './utils/auth'
import Login from './pages/Login'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Employee from './pages/Employee'
import Service from './pages/Service'
import Appointment from './pages/Appointment'
import Schedule from './pages/Schedule'
import Consumable from './pages/Consumable'
import Usage from './pages/Usage'

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="employee" element={<Employee />} />
        <Route path="service" element={<Service />} />
        <Route path="appointment" element={<Appointment />} />
        <Route path="schedule" element={<Schedule />} />
        <Route path="consumable" element={<Consumable />} />
        <Route path="usage" element={<Usage />} />
      </Route>
    </Routes>
  )
}

export default App
