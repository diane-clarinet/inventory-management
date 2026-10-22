<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" type="button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-meta">
                SKU: {{ backlogItem.item_sku }}
                <span class="sep">|</span>
                {{ t('purchaseOrder.shortage') }}: {{ shortage }}
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="viewLoading" class="state-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="viewError" class="error-message">{{ viewError }}</div>
              <div v-else-if="po" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                  <div class="info-value mono">{{ po.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ po.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ po.quantity }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCostShort') }}</div>
                  <div class="info-value">{{ money(po.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value">{{ money(po.quantity * po.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(po.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="badge">{{ po.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(po.created_date) }}</div>
                </div>
                <div class="info-item full">
                  <div class="info-label">{{ t('purchaseOrder.notesLabel') }}</div>
                  <div class="info-value">{{ po.notes || t('purchaseOrder.none') }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="submit">
              <label class="field">
                <span class="info-label">{{ t('purchaseOrder.supplier') }}</span>
                <input v-model="form.supplier_name" type="text" required />
              </label>
              <div class="field-row">
                <label class="field">
                  <span class="info-label">{{ t('purchaseOrder.quantity') }}</span>
                  <input v-model.number="form.quantity" type="number" min="1" step="1" required />
                </label>
                <label class="field">
                  <span class="info-label">{{ t('purchaseOrder.unitCost') }}</span>
                  <input v-model.number="form.unit_cost" type="number" min="0" step="0.01" required />
                </label>
              </div>
              <label class="field">
                <span class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</span>
                <input v-model="form.expected_delivery_date" type="date" required />
              </label>
              <label class="field">
                <span class="info-label">{{ t('purchaseOrder.notes') }}</span>
                <textarea v-model="form.notes" rows="3"></textarea>
              </label>
              <div class="total-row">
                <span class="info-label">{{ t('purchaseOrder.total') }}</span>
                <span class="total-value">{{ money(total) }}</span>
              </div>
              <div v-if="submitError" class="error-message">{{ submitError }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              class="btn-primary"
              type="submit"
              form="po-form"
              :disabled="!isValid || submitting"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' }
})

const emit = defineEmits(['close', 'po-created'])

const { t, currentCurrency, translateProductName } = useI18n()

const emptyForm = () => ({
  supplier_name: '',
  quantity: 1,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

const form = ref(emptyForm())
const submitting = ref(false)
const submitError = ref(null)
const po = ref(null)
const viewLoading = ref(false)
const viewError = ref(null)

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
})

const total = computed(() => {
  const q = Number(form.value.quantity)
  const c = Number(form.value.unit_cost)
  if (!Number.isFinite(q) || !Number.isFinite(c) || form.value.unit_cost === null || form.value.unit_cost === '') return 0
  return q * c
})

const isValid = computed(() => {
  const f = form.value
  const q = Number(f.quantity)
  const c = f.unit_cost === null || f.unit_cost === '' ? NaN : Number(f.unit_cost)
  return (
    f.supplier_name.trim().length > 0 &&
    Number.isInteger(q) && q >= 1 &&
    Number.isFinite(c) && c >= 0 &&
    !!f.expected_delivery_date
  )
})

const money = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

const formatDate = (s) => {
  if (!s) return 'N/A'
  const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(s) ? `${s}T00:00:00` : s)
  if (isNaN(date.getTime())) return s
  return date.toLocaleDateString(currentCurrency.value === 'JPY' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

const loadPO = async () => {
  viewLoading.value = true
  viewError.value = null
  po.value = null
  const itemId = props.backlogItem.id
  try {
    const result = await api.getPurchaseOrderByBacklogItem(itemId)
    if (props.backlogItem?.id !== itemId) return
    po.value = result
  } catch (err) {
    if (props.backlogItem?.id !== itemId) return
    viewError.value = err.response?.data?.detail || t('purchaseOrder.loadError')
    console.error('Failed to load purchase order:', err)
  } finally {
    if (props.backlogItem?.id === itemId) viewLoading.value = false
  }
}

watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  ([open]) => {
    if (!open || !props.backlogItem) return
    submitError.value = null
    submitting.value = false
    if (props.mode === 'view') {
      loadPO()
    } else {
      form.value = emptyForm()
      form.value.quantity = Math.max(1, shortage.value)
    }
  },
  { immediate: true }
)

const submit = async () => {
  if (!isValid.value || submitting.value) return
  submitting.value = true
  submitError.value = null
  try {
    const created = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name.trim(),
      quantity: Number(form.value.quantity),
      unit_cost: Number(form.value.unit_cost),
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes.trim() || null
    })
    emit('po-created', created)
  } catch (err) {
    const detail = err.response?.data?.detail
    submitError.value = typeof detail === 'string' ? detail : t('purchaseOrder.createError')
    console.error('Failed to create purchase order:', err)
  } finally {
    submitting.value = false
  }
}

const close = () => emit('close')
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgb(15 23 42 / 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: white;
  border-radius: var(--radius-md);
  border: var(--border-pop);
  box-shadow: var(--shadow-pop);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5);
  border-bottom: 1px solid var(--ink-200);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ink-900);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--ink-500);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--ink-100);
  color: var(--ink-900);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.item-summary {
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--ink-200);
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--ink-900);
  margin-bottom: var(--space-2);
}

.item-meta {
  font-size: 0.875rem;
  color: var(--ink-500);
  font-family: 'Monaco', 'Courier New', monospace;
}

.sep {
  margin: 0 var(--space-2);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-5);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-item.full {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-500);
}

.info-value {
  font-size: 0.938rem;
  color: var(--ink-900);
  font-weight: 500;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--info);
}

.badge {
  display: inline-block;
  padding: 2px var(--space-3);
  border-radius: 6px;
  background: var(--info-bg);
  color: var(--info-ink);
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

.field-row {
  display: flex;
  gap: var(--space-4);
}

.field input,
.field textarea {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--ink-200);
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: var(--ink-900);
  background: white;
}

.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--ink-500);
}

.field textarea {
  resize: vertical;
}

.total-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  background: var(--ink-100);
  border-radius: 8px;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ink-900);
}

.state-message {
  color: var(--ink-500);
  font-size: 0.938rem;
}

.error-message {
  padding: var(--space-3) var(--space-4);
  background: var(--danger-bg);
  color: var(--danger-ink);
  border-radius: 8px;
  font-size: 0.875rem;
}

.modal-footer {
  padding: var(--space-5);
  border-top: 1px solid var(--ink-200);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary,
.btn-primary {
  padding: var(--space-2) var(--space-4);
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: var(--ink-100);
  border: 1px solid var(--ink-200);
  color: var(--ink-700);
}

.btn-secondary:hover {
  background: var(--ink-200);
  border-color: var(--ink-300);
}

.btn-primary {
  background: var(--ink-900);
  border: 1px solid var(--ink-900);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--ink-700);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
