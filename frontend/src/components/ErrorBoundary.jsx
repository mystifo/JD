import { Component } from "react";

import { Button } from "./ui/Button";

export class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Log only the code-level cause; never request bodies or private content.
    console.error("ui_error", { name: error?.name, message: error?.message });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" className="container" style={{ paddingBlock: "var(--space-7)" }}>
          <h1>Something went wrong</h1>
          <p style={{ marginBlock: "var(--space-3)" }}>
            Your space couldn&apos;t load. Reloading usually fixes it.
          </p>
          <Button onClick={() => window.location.reload()}>Reload HerSpace</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
