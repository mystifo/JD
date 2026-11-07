import { Link, useLocation } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { routeTitle } from "../../utils/routeTitle";

export default function ComingSoon() {
  const { pathname } = useLocation();
  const title = routeTitle(pathname);

  return (
    <div>
      <PageHeader title={title} description="This part of your space is still being built." />
      <Card>
        <EmptyState
          title="On its way"
          body="The layout and navigation are ready. This module arrives with a later milestone; nothing else in your space is affected."
          action={
            <Button as={Link} to="/app" variant="secondary">
              Back to Today
            </Button>
          }
        />
      </Card>
    </div>
  );
}
