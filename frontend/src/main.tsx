import React from "react"
import ReactDOM from "react-dom/client"
import Layout from "./Layout.tsx"
import {
  createBrowserRouter,
  RouterProvider
} from "react-router-dom"
import "./index.css"
import CreateGame from "./pages/CreateGame.tsx"
import JoinGame from "./pages/JoinGame.tsx"

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      {
        index: true,
        element: <JoinGame />
      },
      {
        path: "/join",
        element: <JoinGame />
      },
      {
        path: "/create",
        element: <CreateGame />
      }
    ]
  }
])

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
