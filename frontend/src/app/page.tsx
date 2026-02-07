"use client";

import type { ComponentType } from "react";
import LogoLoop from "@/components/LogoLoop";

const LOGO_IMAGES = [
  { src: "/Hover and Click me (1).png", alt: "Logo 1" },
  { src: "/Hover and Click me (2).png", alt: "Logo 2" },
  { src: "/Hover and Click me (3).png", alt: "Logo 3" },
  { src: "/Hover and Click me (4).png", alt: "Logo 4" },
];

type LogoLoopProps = {
  logos: typeof LOGO_IMAGES;
  speed?: number;
  direction?: string;
  width?: string | number;
  logoHeight?: number;
  gap?: number;
  ariaLabel?: string;
};
const LogoLoopTyped = LogoLoop as ComponentType<LogoLoopProps>;

export default function Home() {
  return (
    <div className="fixed inset-0 h-screen w-screen bg-black">
      <video
        src="/compass.mp4"
        autoPlay
        muted
        playsInline
        loop
        className="absolute inset-0 h-full w-full object-cover"
      />
      <header className="pointer-events-none absolute right-0 top-0 -mt-[22px] pr-28">
        <div className="flex flex-col items-end pt-60">
          <div className="relative inline-block">
            <div className="absolute bottom-full left-0 right-0 mb-1 flex w-full justify-center">
              <div className="w-3/4 min-w-0 overflow-hidden">
                <LogoLoopTyped
                  logos={LOGO_IMAGES}
                  speed={40}
                  direction="left"
                  width="100%"
                  logoHeight={55}
                  gap={24}
                  ariaLabel="Logo loop"
                />
              </div>
            </div>
            <h1
              className="text-right text-4xl font-normal tracking-tight text-white sm:text-5xl md:text-7xl lg:text-8xl xl:text-9xl 2xl:text-[10rem]"
              style={{ fontFamily: "Array, sans-serif" }}
            >
              Compass
            </h1>
          </div>
          <div
            className="mt-2 w-full text-center text-2xl font-normal text-white md:text-3xl lg:text-4xl"
            style={{ fontFamily: "Zodiak, sans-serif" }}
          >
            <p>See Insights Clearer</p>
          </div>
        </div>
      </header>
    </div>
  );
}
