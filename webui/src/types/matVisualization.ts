export interface MatVariable {
  name: string
  shape: number[]
  dtype: string
  data: unknown
}

export interface MatVisualizationResponse {
  filePath: string
  variables: MatVariable[]
}
