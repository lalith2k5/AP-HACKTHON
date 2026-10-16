import { Suspense } from "react";
import IncidentDetailClient from "./incident-detail-client";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground">Loading incident…</div>
      }
    >
      <IncidentDetailClient />
    </Suspense>
  );
}
