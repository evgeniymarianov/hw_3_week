const STATUS_LABELS = {
  paid: 'Оплачен',
  completed: 'Доставлен',
  courier_searching: 'Ищем курьера',
  courier_found: 'Курьер найден',
  courier_arrived_to_darkstore: 'Курьер у даркстора',
  delivering: 'В пути',
}

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || status || 'нет данных'
}
