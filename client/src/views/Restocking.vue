<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ fmt(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          min="0"
          max="100000"
          step="500"
          class="budget-slider"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ fmt(0) }}</span>
          <span class="hint">{{ t('restocking.budgetHint') }}</span>
          <span>{{ fmt(100000) }}</span>
        </div>

        <label class="buffer-toggle">
          <input type="checkbox" v-model="buyAhead" />
          <span>
            <strong>{{ t('restocking.buyAhead') }}</strong>
            <span class="buffer-help">{{ t('restocking.buyAheadHelp', { days: PEAK_DELAY_DAYS }) }}</span>
          </span>
        </label>

        <div v-if="!buyAhead && budgetCoversGap" class="notice info" role="status">
          {{ t('restocking.coversAll', { gapTotal: fmt(gapTotal, 2), unspent: fmt(Math.max(0, budget - plannedTotal), 2) }) }}
        </div>
        <div v-else-if="!buyAhead" class="notice" role="status">
          {{ t('restocking.limiting', { amount: fmt(gapTotal - budget, 2) }) }}
        </div>
        <div v-else-if="unspent >= 0.005" class="notice" role="status">
          {{ t('restocking.bufferUnspent', { amount: fmt(unspent, 2) }) }}
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendation') }} ({{ rows.length }})</h3>
        </div>

        <div v-if="rows.length === 0" class="empty">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-check">{{ t('restocking.table.select') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.item_sku">
                <td class="col-check">
                  <input type="checkbox" v-model="row.selected" :aria-label="row.item_name" />
                </td>
                <td>
                  <strong>{{ row.item_name }}</strong>
                  <div class="sku">{{ row.item_sku }}</div>
                  <span v-if="row.demand_qty === 0" class="tag-buffer">{{ t('restocking.bufferRow') }}</span>
                </td>
                <td>{{ row.supplier }}</td>
                <td class="num">{{ fmt(row.unit_cost, 2) }}</td>
                <td class="num">{{ row.lead_time_days }}</td>
                <td class="num">
                  <input
                    type="number"
                    min="1"
                    step="1"
                    class="qty-input"
                    :class="{ invalid: !isValidQty(row.quantity) }"
                    v-model.number="row.quantity"
                  />
                  <div v-if="buyAhead && row.quantity === row.demand_qty + row.buffer_qty" class="qty-split">
                    {{ t('restocking.split', { demand: row.demand_qty, buffer: row.buffer_qty }) }}
                  </div>
                </td>
                <td class="num"><strong>{{ fmt(lineTotal(row), 2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="summary">
          <div class="summary-line">
            <span>{{ t('restocking.selectedTotal') }}</span>
            <strong :class="{ over: overBudget }">{{ fmt(selectedTotal, 2) }}</strong>
            <span class="of-budget">/ {{ fmt(budget) }}</span>
          </div>
          <div v-if="!overBudget" class="summary-line muted">
            <span>{{ t('restocking.remaining') }}</span>
            <strong>{{ fmt(budget - selectedTotal, 2) }}</strong>
          </div>
          <div v-if="overBudget" class="warning" role="alert">
            {{ t('restocking.overBudget', { amount: fmt(selectedTotal - budget, 2) }) }}
          </div>
          <button class="place-order" :disabled="!canPlace" @click="placeOrder">
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="confirmation" class="confirmation" role="status">
          <strong>{{ t('restocking.successTitle') }}</strong>
          <div>{{ t('restocking.successMessage', { orderNumber: confirmation.order_number, days: confirmation.lead_time_days }) }}</div>
        </div>
        <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Extra days of cover assumed for supplier delays in an upcoming peak season
const PEAK_DELAY_DAYS = 14

const demandGap = (f) => f.forecasted_demand - f.current_demand

// Cost of filling every positive demand gap in full (independent of budget)
function gapCost(forecasts) {
  return forecasts.reduce((sum, f) => {
    const gap = demandGap(f)
    return gap > 0 && f.unit_cost > 0 ? sum + gap * f.unit_cost : sum
  }, 0)
}

// Pure recommendation: greedy fill by demand gap (descending), then an
// optional peak-season buffer with whatever budget is left.
function recommend(forecasts, budget, { buffer = false } = {}) {
  const byPriority = (a, b) =>
    (b.gap - a.gap) || (b.f.forecasted_demand - a.f.forecasted_demand)
  const ranked = forecasts
    .filter(f => f.unit_cost > 0)
    .map(f => ({ f, gap: demandGap(f) }))

  let remaining = budget
  const bySku = new Map()
  const result = []
  const add = (f, demandQty, bufferQty) => {
    const quantity = demandQty + bufferQty
    remaining -= quantity * f.unit_cost
    const existing = bySku.get(f.item_sku)
    if (existing) {
      existing.buffer_qty += bufferQty
      existing.quantity += bufferQty
      return
    }
    const row = {
      item_sku: f.item_sku,
      item_name: f.item_name,
      supplier: f.supplier,
      unit_cost: f.unit_cost,
      lead_time_days: f.lead_time_days,
      demand_qty: demandQty,
      buffer_qty: bufferQty,
      quantity,
      selected: true
    }
    bySku.set(f.item_sku, row)
    result.push(row)
  }

  for (const { f, gap } of ranked.filter(x => x.gap > 0).sort(byPriority)) {
    let quantity = gap
    if (quantity * f.unit_cost > remaining) {
      quantity = Math.floor(remaining / f.unit_cost)
    }
    if (quantity < 1) continue
    add(f, quantity, 0)
  }

  if (buffer) {
    for (const { f } of ranked.filter(x => x.f.trend !== 'decreasing').sort(byPriority)) {
      const target = Math.ceil(f.forecasted_demand / 30 * (f.lead_time_days + PEAK_DELAY_DAYS))
      const quantity = Math.min(target, Math.floor(remaining / f.unit_cost))
      if (!(quantity >= 1)) continue
      add(f, 0, quantity)
    }
  }
  return result
}

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(10000)
    const rows = ref([])
    const buyAhead = ref(false)
    const plannedTotal = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    const fmt = (amount, decimals = 0) =>
      formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)

    const isValidQty = (q) => Number.isInteger(q) && q >= 1
    const lineTotal = (row) => (isValidQty(row.quantity) ? row.quantity * row.unit_cost : 0)

    // Recompute only when the slider moves or data loads
    const rebuild = () => {
      rows.value = recommend(forecasts.value, Number(budget.value) || 0, { buffer: buyAhead.value })
      plannedTotal.value = rows.value.reduce((sum, r) => sum + r.quantity * r.unit_cost, 0)
    }
    watch([budget, buyAhead], rebuild)

    const gapTotal = computed(() => gapCost(forecasts.value))
    const budgetCoversGap = computed(() => (Number(budget.value) || 0) >= gapTotal.value)
    const unspent = computed(() => (Number(budget.value) || 0) - plannedTotal.value)

    const selectedRows = computed(() => rows.value.filter(r => r.selected))
    const selectedTotal = computed(() =>
      selectedRows.value.reduce((sum, r) => sum + lineTotal(r), 0)
    )
    const overBudget = computed(() => selectedTotal.value > budget.value + 1e-9)
    const canPlace = computed(() =>
      !submitting.value &&
      selectedRows.value.length > 0 &&
      selectedRows.value.every(r => isValidQty(r.quantity)) &&
      !overBudget.value
    )

    const placeOrder = async () => {
      if (!canPlace.value) return
      submitting.value = true
      submitError.value = null
      confirmation.value = null
      try {
        confirmation.value = await api.createRestockOrder({
          budget: budget.value,
          items: selectedRows.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.quantity,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days
          }))
        })
      } catch (err) {
        const detail = err.response?.data?.detail
        submitError.value = typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map(d => d.msg).join('; ')
            : `${t('restocking.failed')}: ${err.message}`
      } finally {
        submitting.value = false
      }
    }

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        rebuild()
      } catch (err) {
        error.value = t('restocking.loadFailed') + err.message
      } finally {
        loading.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      budget,
      rows,
      buyAhead,
      PEAK_DELAY_DAYS,
      gapTotal,
      budgetCoversGap,
      plannedTotal,
      unspent,
      fmt,
      isValidQty,
      lineTotal,
      selectedTotal,
      overBudget,
      canPlace,
      submitting,
      submitError,
      confirmation,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--ink-900);
}

.budget-slider {
  width: 100%;
  accent-color: var(--ink-600);
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: var(--ink-500);
  margin-top: var(--space-1);
}

.hint {
  font-style: italic;
}

.buffer-toggle {
  display: flex;
  gap: var(--space-2);
  align-items: flex-start;
  margin-top: var(--space-4);
  color: var(--ink-900);
  font-size: 0.875rem;
  cursor: pointer;
}

.buffer-toggle input {
  margin-top: 3px;
  accent-color: var(--ink-600);
}

.buffer-help {
  display: block;
  color: var(--ink-500);
  margin-top: 2px;
}

.notice {
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--ink-100);
  border: 1px solid var(--ink-200);
  border-radius: 6px;
  color: var(--ink-700);
  font-size: 0.875rem;
}

.notice.info {
  background: var(--info-bg);
  border-color: var(--info-bg);
  border-left: 4px solid var(--info);
  color: var(--info-ink);
}

.tag-buffer {
  display: inline-block;
  margin-top: 2px;
  padding: 0 var(--space-2);
  border-radius: 4px;
  background: var(--ink-100);
  border: 1px solid var(--ink-300);
  color: var(--ink-700);
  font-size: 0.688rem;
  font-weight: 600;
}

.qty-split {
  margin-top: 2px;
  font-size: 0.75rem;
  color: var(--ink-500);
}

.num {
  text-align: right;
}

.col-check {
  width: 70px;
  text-align: center;
}

.sku {
  font-size: 0.75rem;
  color: var(--ink-500);
}

.qty-input {
  width: 90px;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--ink-300);
  border-radius: 6px;
  text-align: right;
  font-size: 0.875rem;
  color: var(--ink-900);
}

.qty-input.invalid {
  border-color: var(--danger);
  background: var(--danger-bg);
}

.empty {
  padding: var(--space-6);
  text-align: center;
  color: var(--ink-500);
}

.summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--ink-200);
}

.summary-line {
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
  color: var(--ink-700);
}

.summary-line strong {
  font-size: 1.125rem;
  color: var(--ink-900);
}

.summary-line strong.over {
  color: var(--danger);
}

.summary-line.muted {
  font-size: 0.875rem;
  color: var(--ink-500);
}

.summary-line.muted strong {
  font-size: 0.875rem;
}

.of-budget {
  color: var(--ink-500);
}

.warning {
  background: var(--danger-bg);
  border: 1px solid #fecaca;
  color: var(--danger-ink);
  padding: var(--space-2) var(--space-3);
  border-radius: 6px;
  font-size: 0.875rem;
}

.place-order {
  background: var(--ink-900);
  color: white;
  border: none;
  border-radius: 6px;
  padding: var(--space-2) var(--space-5);
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order:hover:not(:disabled) {
  background: var(--ink-700);
}

.place-order:disabled {
  background: var(--ink-300);
  cursor: not-allowed;
}

.confirmation {
  margin-top: var(--space-4);
  background: var(--ink-100);
  border: 1px solid var(--ink-300);
  border-left: 4px solid var(--success);
  color: var(--ink-900);
  padding: var(--space-3) var(--space-4);
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
