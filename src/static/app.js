document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const signupContainer = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");
  const loginButton = document.getElementById("login-button");
  const logoutButton = document.getElementById("logout-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const teacherAccessMessage = document.getElementById("teacher-access-message");
  let sessionToken = null;

  function setLoggedIn(loggedIn) {
    signupContainer.hidden = !loggedIn;
    teacherAccessMessage.hidden = loggedIn;
    loginButton.hidden = loggedIn;
    logoutButton.hidden = !loggedIn;
  }

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");
    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function handleExpiredSession() {
    sessionToken = null;
    setLoggedIn(false);
    teacherAccessMessage.textContent =
      "Your teacher session has expired. Log in again to manage registrations.";
    fetchActivities();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error("The activity list could not be loaded.");
      }

      const activities = await response.json();
      activitiesList.replaceChildren();
      activitySelect.replaceChildren(new Option("-- Select an activity --", ""));

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const title = document.createElement("h4");
        title.textContent = name;
        activityCard.appendChild(title);

        const description = document.createElement("p");
        description.textContent = details.description;
        activityCard.appendChild(description);

        const schedule = document.createElement("p");
        const scheduleLabel = document.createElement("strong");
        scheduleLabel.textContent = "Schedule: ";
        schedule.append(scheduleLabel, details.schedule);
        activityCard.appendChild(schedule);

        const spotsLeft = details.max_participants - details.participants.length;
        const availability = document.createElement("p");
        const availabilityLabel = document.createElement("strong");
        availabilityLabel.textContent = "Availability: ";
        availability.append(availabilityLabel, `${spotsLeft} spots left`);
        activityCard.appendChild(availability);

        const participantsContainer = document.createElement("div");
        participantsContainer.className = "participants-container";
        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";
        const participantsTitle = document.createElement("h5");
        participantsTitle.textContent = "Participants:";
        participantsSection.appendChild(participantsTitle);

        if (details.participants.length > 0) {
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";

          details.participants.forEach((email) => {
            const participant = document.createElement("li");
            const participantEmail = document.createElement("span");
            participantEmail.className = "participant-email";
            participantEmail.textContent = email;
            participant.appendChild(participantEmail);

            if (sessionToken) {
              const removeButton = document.createElement("button");
              removeButton.className = "delete-btn";
              removeButton.type = "button";
              removeButton.textContent = "Remove";
              removeButton.setAttribute(
                "aria-label",
                `Unregister ${email} from ${name}`
              );
              removeButton.addEventListener("click", () =>
                handleUnregister(name, email)
              );
              participant.appendChild(removeButton);
            }

            participantsList.appendChild(participant);
          });
          participantsSection.appendChild(participantsList);
        } else {
          const emptyMessage = document.createElement("p");
          emptyMessage.textContent = "No participants yet";
          participantsSection.appendChild(emptyMessage);
        }

        participantsContainer.appendChild(participantsSection);
        activityCard.appendChild(participantsContainer);
        activitiesList.appendChild(activityCard);

        activitySelect.add(new Option(name, name));
      });
    } catch (error) {
      activitiesList.replaceChildren();
      const errorMessage = document.createElement("p");
      errorMessage.textContent = "Failed to load activities. Please try again later.";
      activitiesList.appendChild(errorMessage);
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(activity, email) {
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${sessionToken}` },
        }
      );
      const result = await response.json();

      if (response.status === 401) {
        handleExpiredSession();
        return;
      }
      if (!response.ok) {
        showMessage(result.detail || "Could not unregister the student.", "error");
        return;
      }

      showMessage(result.message, "success");
      await fetchActivities();
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  loginButton.addEventListener("click", () => {
    loginError.classList.add("hidden");
    loginDialog.showModal();
  });

  document.getElementById("close-login-button").addEventListener("click", () => {
    loginDialog.close();
  });

  loginDialog.addEventListener("click", (event) => {
    if (event.target === loginDialog) {
      loginDialog.close();
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.classList.add("hidden");

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: document.getElementById("login-username").value,
          password: document.getElementById("login-password").value,
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Login failed.");
      }

      sessionToken = result.access_token;
      setLoggedIn(true);
      loginForm.reset();
      loginDialog.close();
      teacherAccessMessage.textContent =
        "Teacher login is required to register or unregister students.";
      await fetchActivities();
    } catch (error) {
      loginError.textContent = error.message;
      loginError.classList.remove("hidden");
      console.error("Error logging in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${sessionToken}` },
      });

      if (response.status === 401) {
        handleExpiredSession();
        return;
      }

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Logout failed.");
      }

      sessionToken = null;
      setLoggedIn(false);
      teacherAccessMessage.textContent = "You have been logged out.";
      await fetchActivities();
    } catch (error) {
      showMessage("Failed to log out. Please try again.", "error");
      console.error("Error logging out:", error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${sessionToken}` },
        }
      );
      const result = await response.json();

      if (response.status === 401) {
        handleExpiredSession();
        return;
      }
      if (!response.ok) {
        showMessage(result.detail || "Could not sign up the student.", "error");
        return;
      }

      showMessage(result.message, "success");
      signupForm.reset();
      await fetchActivities();
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  setLoggedIn(false);
  fetchActivities();
});
