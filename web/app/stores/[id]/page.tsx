import { Suspense } from "react";
import StoreDetailClient from "./store-detail-client";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-muted-foreground">Loading store...</div>}>
      <StoreDetailClient />
    </Suspense>
  );
}
