// File: frontend/src/features/recommendations/useRecommendations.ts
import { useMutation } from "@tanstack/react-query";

import { recommendationApi } from "@/api/endpoints";
import type { ProductLine, RecommendationResponse } from "@/types/domain";

export function useRecommend() {
  return useMutation<
    RecommendationResponse,
    Error,
    { product_line?: ProductLine; weights?: Record<string, number>; top_k?: number } | undefined
  >({
    mutationFn: (params) => recommendationApi.recommend(params),
  });
}
