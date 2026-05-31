import { FormEvent, useCallback, useEffect, useState } from 'react'

import { Sidebar } from '../../components/layout/Sidebar'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useAuth } from '../../hooks/useAuth'
import { getApiErrorMessage } from '../../services/apiError'
import scraperService, {
  CreateScraperSourceData,
  LayoutPattern,
  ScraperRun,
  ScraperSource,
} from '../../services/scraper.service'

const EMPTY_SOURCE: CreateScraperSourceData = {
  name: '',
  base_url: '',
  robots_txt_url: '',
  data_type: 'text/html',
  source_category: 'layout_pattern_reference',
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : 'Not checked'
}

function statusClasses(status: string) {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-red-100 text-red-700'
  return 'bg-amber-100 text-amber-700'
}

export default function ScraperPage() {
  const { logOut, user } = useAuth()
  const [sources, setSources] = useState<ScraperSource[]>([])
  const [runs, setRuns] = useState<ScraperRun[]>([])
  const [patterns, setPatterns] = useState<LayoutPattern[]>([])
  const [latestRun, setLatestRun] = useState<ScraperRun | null>(null)
  const [form, setForm] = useState<CreateScraperSourceData>(EMPTY_SOURCE)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [runningSourceId, setRunningSourceId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [sourceData, runData, patternData, statusData] = await Promise.all([
      scraperService.sources(),
      scraperService.runs(),
      scraperService.patterns(),
      scraperService.status().catch(() => null),
    ])
    setSources(sourceData)
    setRuns(runData)
    setPatterns(patternData)
    setLatestRun(statusData)
  }, [])

  useEffect(() => {
    refresh()
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load scraper pipeline')))
      .finally(() => setLoading(false))
  }, [refresh])

  async function handleCreateSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const created = await scraperService.createSource(form)
      setSources((current) => [created, ...current])
      setForm(EMPTY_SOURCE)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to add scraper source'))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRun(sourceId: string) {
    setRunningSourceId(sourceId)
    setError(null)
    try {
      await scraperService.run(sourceId)
      await refresh()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to run scraper source'))
    } finally {
      setRunningSourceId(null)
    }
  }

  async function handleDelete(sourceId: string) {
    setError(null)
    try {
      await scraperService.deleteSource(sourceId)
      setSources((current) => current.filter((source) => source.id !== sourceId))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to delete scraper source'))
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar userName={user?.name} userEmail={user?.email} onLogout={logOut} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Data Pipeline</h1>
          <p className="mt-1 text-sm text-gray-500">
            Public text reference sources for future layout learning.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Add Public Text Source</h2>
          <form className="grid gap-3 lg:grid-cols-5" onSubmit={handleCreateSource}>
            <Input
              label="Source name"
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
            <Input
              label="Public URL"
              required
              type="url"
              value={form.base_url}
              onChange={(event) => setForm({ ...form, base_url: event.target.value })}
            />
            <Input
              label="robots.txt URL"
              required
              type="url"
              value={form.robots_txt_url}
              onChange={(event) => setForm({ ...form, robots_txt_url: event.target.value })}
            />
            <Input
              label="Category"
              required
              value={form.source_category}
              onChange={(event) => setForm({ ...form, source_category: event.target.value })}
            />
            <div className="flex items-end">
              <Button type="submit" loading={submitting} className="w-full">
                Add Source
              </Button>
            </div>
          </form>
        </section>

        {loading ? (
          <p className="py-12 text-center text-gray-400">Loading pipeline...</p>
        ) : (
          <>
            <section className="mb-6 rounded-lg border border-gray-200 bg-white">
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                <h2 className="text-base font-semibold text-gray-900">Sources</h2>
                <span className="text-xs text-gray-500">{sources.length} registered</span>
              </div>
              {sources.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-gray-400">No public text sources registered.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                      <tr>
                        <th className="px-4 py-3">Source</th>
                        <th className="px-4 py-3">Category</th>
                        <th className="px-4 py-3">robots.txt</th>
                        <th className="px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {sources.map((source) => (
                        <tr key={source.id}>
                          <td className="px-4 py-3">
                            <p className="font-medium text-gray-900">{source.name}</p>
                            <p className="max-w-md truncate text-xs text-gray-500">{source.base_url}</p>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{source.source_category}</td>
                          <td className="px-4 py-3 text-gray-600">{formatDate(source.last_checked)}</td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <Button
                                className="text-xs"
                                loading={runningSourceId === source.id}
                                onClick={() => handleRun(source.id)}
                              >
                                Run
                              </Button>
                              <Button
                                className="text-xs"
                                variant="secondary"
                                onClick={() => handleDelete(source.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <div className="mb-6 grid gap-6 xl:grid-cols-2">
              <section className="rounded-lg border border-gray-200 bg-white">
                <div className="border-b border-gray-200 px-4 py-3">
                  <h2 className="text-base font-semibold text-gray-900">Latest Status</h2>
                </div>
                {!latestRun ? (
                  <p className="px-4 py-8 text-sm text-gray-400">No scraper runs yet.</p>
                ) : (
                  <div className="space-y-2 px-4 py-4 text-sm text-gray-600">
                    <span className={`inline-flex rounded px-2 py-1 text-xs font-medium ${statusClasses(latestRun.status)}`}>
                      {latestRun.status}
                    </span>
                    <p>{latestRun.records_collected} records collected</p>
                    <p>{formatDate(latestRun.completed_at ?? latestRun.started_at)}</p>
                    {latestRun.error_message && <p className="text-red-600">{latestRun.error_message}</p>}
                  </div>
                )}
              </section>

              <section className="rounded-lg border border-gray-200 bg-white">
                <div className="border-b border-gray-200 px-4 py-3">
                  <h2 className="text-base font-semibold text-gray-900">Run History</h2>
                </div>
                {runs.length === 0 ? (
                  <p className="px-4 py-8 text-sm text-gray-400">No scraper runs yet.</p>
                ) : (
                  <ul className="divide-y divide-gray-100">
                    {runs.slice(0, 8).map((run) => (
                      <li key={run.id} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
                        <div>
                          <p className="font-medium text-gray-700">{formatDate(run.started_at)}</p>
                          <p className="text-xs text-gray-500">{run.records_collected} records</p>
                        </div>
                        <span className={`rounded px-2 py-1 text-xs font-medium ${statusClasses(run.status)}`}>
                          {run.status}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>

            <section className="rounded-lg border border-gray-200 bg-white">
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                <h2 className="text-base font-semibold text-gray-900">Extracted Layout Patterns</h2>
                <span className="text-xs text-gray-500">{patterns.length} references</span>
              </div>
              {patterns.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-gray-400">No structured patterns extracted yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                      <tr>
                        <th className="px-4 py-3">Room</th>
                        <th className="px-4 py-3">Building</th>
                        <th className="px-4 py-3">Area sqm</th>
                        <th className="px-4 py-3">Zone</th>
                        <th className="px-4 py-3">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {patterns.slice(0, 20).map((pattern) => (
                        <tr key={pattern.id}>
                          <td className="px-4 py-3 font-medium text-gray-800">{pattern.room_type ?? 'General'}</td>
                          <td className="px-4 py-3 text-gray-600">{pattern.building_type ?? '-'}</td>
                          <td className="px-4 py-3 text-gray-600">
                            {pattern.typical_area_sqm_min === null
                              ? '-'
                              : `${pattern.typical_area_sqm_min}-${pattern.typical_area_sqm_max}`}
                          </td>
                          <td className="px-4 py-3 text-gray-600">{pattern.zone ?? '-'}</td>
                          <td className="px-4 py-3 text-gray-600">{pattern.confidence}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  )
}
