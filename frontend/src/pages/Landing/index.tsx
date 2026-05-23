import { Link } from 'react-router-dom'

import { Button } from '../../components/ui/Button'

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">ArchiAI</h1>
      <p className="text-gray-600 mb-8">
        AI-powered architectural design in your browser.
      </p>
      <div className="flex gap-4">
        <Link to="/register">
          <Button>Get Started</Button>
        </Link>
        <Link to="/login">
          <Button variant="secondary">Log In</Button>
        </Link>
      </div>
    </main>
  )
}
