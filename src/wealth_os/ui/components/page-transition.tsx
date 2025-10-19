"use client";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import { usePathname } from "next/navigation";
import React from "react";

export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const variants = {
    initial: { opacity: 0, y: 8 },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        opacity: { duration: 0.28, ease: [0.4, 0, 0.2, 1] },
        y: { duration: 0.32, ease: [0.4, 0, 0.2, 1] },
      },
    },
    exit: {
      opacity: 0,
      y: -8,
      transition: {
        opacity: { duration: 0.22, ease: [0.4, 0, 0.2, 1] },
        y: { duration: 0.26, ease: [0.4, 0, 0.2, 1] },
      },
    },
  } as const;

  return (
    <MotionConfig reducedMotion="user">
      <div className="relative">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={pathname}
            // Avoid implicit layout animations that can feel like a second animation
            variants={variants}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ willChange: "opacity, transform" }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </div>
    </MotionConfig>
  );
}
