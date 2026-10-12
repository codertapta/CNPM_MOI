import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Trang chủ AutomaticDubbing", () => {
  it("hiển thị OK khi backend hoạt động", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "ok",
          version: "unknown",
        }),
      }),
    );

    render(<App />);

    expect(await screen.findByText("OK")).toBeInTheDocument();
  });
});
