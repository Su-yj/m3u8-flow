/** 轻量校验，替代 Element Plus FormRules */

export type FieldRule<T> =
  | { required?: true; message: string }
  | { validate: (value: unknown, model: T) => string | null }

export function validateModel<T extends Record<string, unknown>>(
  model: T,
  rules: Partial<Record<keyof T, FieldRule<T>[]>>,
): { valid: true } | { valid: false; message: string } {
  for (const key of Object.keys(rules) as (keyof T)[]) {
    const list = rules[key]
    if (!list?.length) continue
    const value = model[key]
    for (const rule of list) {
      if ('required' in rule && rule.required) {
        const empty =
          value === undefined ||
          value === null ||
          (typeof value === 'string' && !value.trim()) ||
          (typeof value === 'number' && Number.isNaN(value))
        if (empty) {
          return { valid: false, message: rule.message }
        }
        continue
      }
      if ('validate' in rule) {
        const msg = rule.validate(value, model)
        if (msg) {
          return { valid: false, message: msg }
        }
      }
    }
  }
  return { valid: true }
}

export function headersJsonRule<T>(): FieldRule<T> {
  return {
    validate: (value: unknown) => {
      const s = typeof value === 'string' ? value : ''
      if (!s.trim()) return null
      try {
        const parsed = JSON.parse(s) as unknown
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          return null
        }
        return '请求头必须是 JSON 对象'
      } catch {
        return '请求头 JSON 格式不正确'
      }
    },
  }
}
