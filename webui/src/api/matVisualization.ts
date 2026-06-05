import axios from 'axios'

import type { MatVisualizationResponse } from '../types/matVisualization'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export async function fetchMatVisualization(
  filePath: string,
): Promise<MatVisualizationResponse> {
  const response = await api.post<MatVisualizationResponse>('/api/visualization/mat', {
    file_path: filePath,
  })

  return response.data
}
