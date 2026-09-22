export const requestStatuses = { pending: 'Awaiting approval', held: 'Stock held', approved: 'Rental approved', collected: 'Rental collected', returned: 'Returned', converted: 'Order created', cancelled: 'Cancelled', rejected: 'Rejected', expired: 'Expired' }
export const requestStatusLabel = value => requestStatuses[value] || value
