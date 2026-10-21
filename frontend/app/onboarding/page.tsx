import OnboardingWizard from "./OnboardingWizard";

export default function OnboardingPage() {
  return (
    <div>
      <div className="page-head">
        <h1>Set up your school workspace</h1>
        <p>Four steps: pick a starting template, enter school details, choose modules, review — then everything is created for you.</p>
      </div>
      <OnboardingWizard />
    </div>
  );
}
