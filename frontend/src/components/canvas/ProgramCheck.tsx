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

const STATUS_DOT: Record<ConstraintStatus, string> = {
  satisfied: 'bg-ok',
  partial: 'bg-warn',
  warning: 'bg-warn',
  failed: 'bg-danger',
  not_evaluated: 'bg-muted-light',
  missing_dependency: 'bg-danger',
}

function CheckRow({ check }: { check: ProgramConstraintCheck }) {
  return (
    <li className="rounded-md bg-graphite-850/80 px-2 py-1.5">
      <div className="flex items-start gap-2">
        <span
          aria-hidden="true"
          className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${STATUS_DOT[check.status]}`}
        />
        <span className="min-w-0 flex-1 text-[10px] leading-4 text-muted">
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
  const selected = selectedRoom
    ? checksForRoom(validation, selectedRoom)
    : null
  const checks = (
    selected
      ? selected.constraints
      : sortedConstraintChecks(validation.constraintChecks)
  ).slice(0, maxChecks)
  const panelStatus = selected
    ? aggregateStatus([
        ...(selected.space ? [selected.space.status] : []),
        ...selected.constraints.map((check) => check.status),
      ])
    : validation.overallStatus

  return (
    <section data-testid="program-check">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-light">
          {selectedRoom ? 'Constraint check' : 'Program check'}
        </p>
        <span
          data-testid="program-check-status"
          className={`text-[10px] font-semibold ${statusTone(panelStatus)}`}
        >
          {statusLabel(panelStatus)}
        </span>
      </div>

      {!selectedRoom && (
        <div className="mt-2 grid grid-cols-2 gap-1.5 rounded-lg bg-graphite-850/80 p-2.5">
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
        <div className="mt-2 flex items-center justify-between rounded-md bg-graphite-850/80 px-2 py-1.5 text-[10px]">
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
        <ul className="mt-2 flex flex-col gap-1">
          {checks.map((check) => <CheckRow key={check.id} check={check} />)}
        </ul>
      ) : (
        <p className="mt-2 text-[10px] leading-4 text-muted-light">
          {selectedRoom
            ? 'No prompt-level constraints target this space.'
            : 'No evaluable constraints were extracted.'}
        </p>
      )}
    </section>
  )
}
