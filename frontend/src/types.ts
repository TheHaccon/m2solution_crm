export type User = {
  id: number
  email: string
  full_name: string
}

export type TeamSummary = {
  id: number
  name: string
  created_at: string
}

export type TeamMember = {
  user_id: number
  email: string
  full_name: string
}

export type TeamDetail = TeamSummary & {
  members: TeamMember[]
}

export type Client = {
  id: number
  name: string
  email: string | null
  phone: string | null
  address: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type LineItem = {
  id: number
  description: string
  quantity: string | number
  unit_price: string | number
  amount: string | number
}

export type InvoiceList = {
  id: number
  client_id: number
  client_name: string
  number: string
  status: string
  issue_date: string
  due_date: string | null
  total: string | number
  view_count: number
  last_viewed_at: string | null
  public_token: string | null
  share_url: string | null
  created_at: string
}

export type Invoice = InvoiceList & {
  client_email: string | null
  client_address: string | null
  notes: string | null
  subtotal: string | number
  sent_at: string | null
  paid_at: string | null
  updated_at: string
  line_items: LineItem[]
}

export type InvoiceView = {
  id: number
  viewed_at: string
  user_agent: string | null
}

export type PublicInvoice = {
  number: string
  status: string
  issue_date: string
  due_date: string | null
  notes: string | null
  subtotal: string | number
  total: string | number
  client_name: string
  client_email: string | null
  client_address: string | null
  line_items: LineItem[]
  company_name: string
  company_email: string
  company_address: string
  company_phone: string
}

export type Meeting = {
  id: number
  client_id: number
  client_name: string
  title: string
  scheduled_at: string
  attendees: string | null
  body: string | null
  created_at: string
  updated_at: string
}

export type Dashboard = {
  unpaid_count: number
  unpaid_total: string | number
  draft_count: number
  paid_count: number
  recent_invoices: {
    id: number
    number: string
    client_name: string
    status: string
    total: string | number
    view_count: number
    due_date: string | null
    issue_date: string | null
  }[]
  recent_meetings: {
    id: number
    title: string
    client_name: string
    scheduled_at: string
  }[]
  recent_views: {
    invoice_id: number
    invoice_number: string
    client_name: string
    viewed_at: string
  }[]
}

export type LineItemInput = {
  description: string
  quantity: number
  unit_price: number
}
