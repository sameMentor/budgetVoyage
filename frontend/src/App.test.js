import { render, screen } from "@testing-library/react";
import App from "./App";

// Minimal smoke tests to validate critical UI surfaces render.
describe("App", () => {
  test("shows navigation logo and hero title", () => {
    render(<App />);
    expect(screen.getByTestId("navbar-logo")).toBeInTheDocument();
    expect(screen.getByTestId("hero-title")).toHaveTextContent(/virtual tour buddy/i);
  });

  test("theme toggle is present", () => {
    render(<App />);
    expect(screen.getByTestId("theme-toggle-btn")).toBeInTheDocument();
  });
});
