import { Outlet } from "react-router-dom";
import Header from "./components/Header";
import LoadingProvider from "./providers/LoadingProvider";

export default function Layout() {
  return (
    <LoadingProvider>
      <div id="root-content">
        <Header />
        <Outlet />
      </div>
    </LoadingProvider>
  );
}
