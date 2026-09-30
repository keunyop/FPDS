import { Suspense } from "react";
import DashboardPage from "@/app/dashboard/page";
import PublicLoading from "@/components/fpds/public/public-route-loading";

export { generateMetadata } from "@/app/dashboard/page";

export default function HomePage(props: Parameters<typeof DashboardPage>[0]) {
  return <Suspense fallback={<PublicLoading />}><DashboardPage {...props} /></Suspense>;
}
