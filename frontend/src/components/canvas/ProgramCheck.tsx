import type { Room } from '../../store/canvasStore'
import {
  checksForRoom,
  sortedConstraintChecks,
  statusLabel,
  statusTone,
  type ConstraintStatus,
  type ProgramConstraintCheck,
  type ProgramValidationResult,
} from './programValidationModel'

interface ProgramCheckProps {
  validation: ProgramValidationResult
  selectedRoom?: Room | null
  maxChecks?: number
}

const STATUS_MARKER: Record<ConstraintStatus, { label: string; tone: string }> = {
  satisfied: { label: 'ok', tone: 'bg-ok' },
  partial: { label: '!', tone: 'bg-warn' },
  warning: { label: '!', tone: 'bg-warn' },
  failed: { label: 'x', tone: 'bg-danger' },
  not_evaluated: { label: '-', tone: 'bg-muted-light' },
  missing_dependency: { label: 'x', tone: 'bg-danger' },
}

function CheckRow({ check }: { check: ProgramConstraintCheck }) {
  const marker = STATUS_MARKER[check.status]
  return (
    <li className="border-b border-ink/10 py-2 last:border-b-0">
      <div className="flex items-start gap-2">
        <span
          aria-hidden="true"
          className={`mt-0.5 inline-flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full text-[8px] font-bold text-[#1b1c1d] ${marker.tone}`}
        >
          {marker.label}
        </span>
        <span className="min-w-0 flex-1 text-[10px] leading-4 text-ink/80">
          {check.label}
        </span>
        <span className={`shrink-0 text-[10px] font-medium ${statusTone(check.status)}`}>
          {statusLabel(check.status)}
        </span>
      </div>
    </li>
  )
}

function aggregateStatus(statuses: ConstraintStatus[]): ConstraintStatus {
  if (statuses.includes('failed')) return 'failed'
  if (statuses.includes('missing_dependency')) return 'missing_dependency'
  if (statuses.includes('warning') || statuses.includes('partial')) return 'warning'
  if (statuses.includes('not_evaluated')) return 'not_evaluated'
  return statuses.length > 0 ? 'satisfied' : 'not_evaluated'
}

export function ProgramCheck({
  validation,
  selectedRoom = null,
  maxChecks = 8,
}: ProgramCheckProps) {
  const selected = selectedRoom ? checksForRoom(validation, selectedRoom) : null
  const checks = (
    selected ? selected.constraints : sortedConstraintChecks(validation.constraintChecks)
  ).slice(0, maxChecks)
  const panelStatus = selected
    ? aggregateStatus([
        ...(selected.space ? [selected.space.status] : []),
        ...selected.constraints.map((check) => check.status),
      ])
    : validation.overallStatus

  return (
    <section
      data-testid="program-check"
      className="rounded-lg border border-ink/10 bg-[#232425]/80 p-3"
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-semibold text-ink">
          {selectedRoom ? 'Constraint Check' : 'Program Check'}
        </p>
        <span
          data-testid="program-check-status"
          className={`text-[10px] font-semibold ${statusTone(panelStatus)}`}
        >
          {statusLabel(panelStatus)}
        </span>
      </div>

      {!selectedRoom && (
        <div className="mt-2 grid grid-cols-2 gap-1.5 rounded-md border border-ink/10 bg-[#1d1e1f]/65 p-2.5">
          <div>
            <p className="text-[9px] uppercase tracking-wide text-muted-light">Requested</p>
            <p className="font-mono text-xs tabular-nums text-ink">
              {validation.summary.requestedSpaceCount}
            </p>
          </div>
          <div>
            <p className="text-[9px] uppercase tracking-wide text-muted-light">Generated</p>
            <p className="font-mono text-xs tabular-nums text-ink">
              {validation.summary.generatedSpaceCount}
            </p>
          </div>
        </div>
      )}

      {selected?.space && (
        <div className="mt-2 flex items-center justify-between rounded-md border border-ink/10 bg-[#1d1e1f]/65 px-2 py-1.5 text-[10px]">
          <span className="truncate text-muted">
            {selected.space.originalLabel || selectedRoom?.label}
          </span>
          <span className={statusTone(selected.space.status)}>
            {selected.space.generatedCount} / {selected.space.requestedCount}
          </span>
        </div>
      )}

      {!selectedRoom && validation.missingSpaces.length > 0 && (
        <p className="mt-2 text-[10px] leading-4 text-danger">
          Missing: {validation.missingSpaces.map((space) => `${space.label} x${space.count}`).join(', ')}
        </p>
      )}
      {!selectedRoom && validation.extraSpaces.length > 0 && (
        <p className="mt-1 text-[10px] leading-4 text-muted-light">
          Added for planning: {validation.extraSpaces.map((space) => `${space.label} x${space.count}`).join(', ')}
        </p>
      )}

      {checks.length > 0 ? (
        <ul className="mt-2 flex flex-col">
          {checks.map((check) => <CheckRow key={check.id} check={check} />)}
        </ul>
      ) : (
        <p className="mt-2 text-[10px] leading-4 text-muted-light">
          {selectedRoom
            ? 'No prompt-level constraints target this space.'
            : 'No evaluable constraints were extracted.'}
        </p>
      )}

      <div className="mt-2 flex items-center justify-center gap-2 rounded-md border border-ink/10 bg-[#1d1e1f]/65 px-2 py-1.5 font-mono text-[9px] tabular-nums">
        <span className="text-ok">{validation.summary.satisfiedCount} satisfied</span>
        <span className="text-muted-light">/</span>
        <span className="text-warn">{validation.summary.warningCount} warnings</span>
        <span className="text-muted-light">/</span>
        <span className="text-danger">{validation.summary.failedCount} failed</span>
      </div>
    </section>
  )
}
