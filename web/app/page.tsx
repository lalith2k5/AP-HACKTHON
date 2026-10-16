"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { motion as motionTokens } from "@/lib/tokens";

export default function WelcomePage() {
  return (
    <main className="relative flex min-h-dvh flex-col items-center justify-center px-6 py-16">
      {/* subtle top glow, Apple-ish material feel */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-40 h-80 bg-[radial-gradient(60%_100%_at_50%_100%,color-mix(in_oklch,var(--primary),transparent_75%),transparent)]"
      />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={motionTokens.spring}
        className="relative w-full max-w-xl"
      >
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              aria-hidden
              className="inline-block size-2.5 rounded-full bg-[var(--primary)] shadow-[0_0_12px_var(--primary)]"
            />
            <span className="text-sm font-medium tracking-tight">StoreSignal AI</span>
          </div>
          <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
            Local · Demo mode
          </span>
        </div>

        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Turning store chatter
          <br />
          into action.
        </h1>
        <p className="mt-4 max-w-md text-base leading-relaxed text-muted-foreground">
          Multilingual retail operations intelligence. Early-warning and
          incident-resolution — not a sentiment dashboard.
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Button
            render={<Link href="/overview" />}
            nativeButton={false}
            size="lg"
            className="h-11 w-full sm:w-auto sm:min-w-[200px]"
          >
            Open sample workspace
            <span className="ml-2 text-xs opacity-70">SIMULATED DATA</span>
          </Button>
          <Button
            render={<Link href="/overview?import=1" />}
            nativeButton={false}
            size="lg"
            variant="outline"
            className="h-11 w-full sm:w-auto sm:min-w-[200px]"
          >
            Import my data
          </Button>
        </div>

        <p className="mt-8 text-xs leading-relaxed text-muted-foreground">
          Demo profile selector is a local simulation, not production identity
          verification. All sample data is simulated; do not enter real customer
          or staff data.
        </p>
      </motion.div>
    </main>
  );
}
