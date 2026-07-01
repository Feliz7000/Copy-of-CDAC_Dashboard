import { redirect } from "next/navigation"
import { auth } from "@/auth"

export default async function Home() {
  const session = await auth();

  if (!session) {
    redirect("/login");
  }

  const role = session.user.role;
  
  switch (role) {
    case "admin":
      redirect("/admin/dashboard");
    case "faculty":
      redirect("/faculty/dashboard");
    case "hod":
      redirect("/hod/dashboard");
    case "student":
      redirect("/student/dashboard");
    default:
      redirect("/login");
  }
}
