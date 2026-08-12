import { createBrowserRouter } from "react-router";
import Shell from "../components/Shell";
import Overview from "../pages/Overview";
import EventControl from "../pages/EventControl";
import RoundRoom from "../pages/RoundRoom";
import DataLab from "../pages/DataLab";
import Experiments from "../pages/Experiments";
import Validation from "../pages/Validation";
import Models from "../pages/Models";
import FeatureLab from "../pages/FeatureLab";
import Ensembles from "../pages/Ensembles";
import Leaderboard from "../pages/Leaderboard";
import Submission from "../pages/Submission";
import Staking from "../pages/Staking";
import ComputeJobs from "../pages/ComputeJobs";
import Repository from "../pages/Repository";
import Documentation from "../pages/Documentation";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Shell,
    children: [
      { index: true, Component: Overview },
      { path: "event", Component: EventControl },
      { path: "round", Component: RoundRoom },
      { path: "data", Component: DataLab },
      { path: "experiments", Component: Experiments },
      { path: "validation", Component: Validation },
      { path: "models", Component: Models },
      { path: "features", Component: FeatureLab },
      { path: "ensembles", Component: Ensembles },
      { path: "leaderboard", Component: Leaderboard },
      { path: "submission", Component: Submission },
      { path: "staking", Component: Staking },
      { path: "compute", Component: ComputeJobs },
      { path: "repository", Component: Repository },
      { path: "docs", Component: Documentation },
    ],
  },
]);
