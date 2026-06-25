export type AssetStatus = "operational" | "maintenance" | "out_of_service" | "decommissioned";
export type WOStatus    = "backlog" | "in_progress" | "pending_parts" | "completed" | "cancelled";
export type WOPriority  = "critical" | "high" | "medium" | "low";
export type WOType      = "preventive" | "corrective" | "ai_triggered" | "calibration" | "emergency";
export type CertStatus  = "valid" | "expired" | "near_expiry";

export interface Asset {
  id: string;
  asset_code: string;
  name: string;
  manufacturer: string;
  model: string;
  serial_number: string;
  category: string;
  status: AssetStatus;
  center_id: string;
  location_room: string;
  rul_score?: number;
  rul_computed_at?: string;
  next_pm_date?: string;
  dicom_ae_title?: string;
  opcua_node_id?: string;
  assigned_technician_id?: string;
  acquisition_cost?: number;
  created_at: string;
  updated_at: string;
}

export interface WorkOrder {
  id: string;
  wo_number: string;
  title: string;
  description?: string;
  status: WOStatus;
  wo_type: WOType;
  priority: WOPriority;
  asset_id: string;
  center_id: string;
  assigned_to_id?: string;
  scheduled_start?: string;
  estimated_hours?: number;
  actual_hours?: number;
  labor_cost?: number;
  parts_cost?: number;
  total_cost?: number;
  checklist?: ChecklistItem[];
  parts_used?: PartUsed[];
  ai_trigger_ref?: string;
  dicom_sr_uid?: string;
  created_at: string;
  updated_at: string;
}

export interface ChecklistItem { label: string; completed: boolean; }
export interface PartUsed { name: string; qty: number; unit_cost: number; }

export interface AIInference {
  id: string;
  asset_id: string;
  agent_id: string;
  rul_days?: number;
  anomaly_score?: number;
  confidence?: number;
  shap_values?: Record<string, number>;
  model_version: string;
  created_at: string;
}

export interface CalibrationCert {
  id: string;
  asset_id: string;
  cert_type: string;
  cert_number: string;
  issue_date: string;
  expiry_date: string;
  status: CertStatus;
  issuing_body?: string;
  pdf_url?: string;
  created_at: string;
}

export interface CostSummary {
  total: number;
  breakdown: Record<string, number>;
  period?: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  center_id?: string;
  is_active: boolean;
}
