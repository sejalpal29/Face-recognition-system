// Frontend Integration Examples for AI Surveillance Dashboard API
// Base URL: http://localhost:8000

const API_BASE_URL = "http://localhost:8000/api"

// ==========================================
// 1. LOAD DASHBOARD STATISTICS
// ==========================================
async function loadDashboardStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/statistics`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const data = await response.json()
    const stats = data.statistics

    console.log("[v0] Dashboard Stats:", stats)

    // Update UI with stats
    document.getElementById("total-persons").textContent = stats.total_registered_persons
    document.getElementById("total-embeddings").textContent = stats.total_facial_embeddings
    document.getElementById("device").textContent = stats.device
    document.getElementById("match-threshold").textContent = stats.match_threshold

    return stats
  } catch (error) {
    console.error("[v0] Error loading dashboard stats:", error)
  }
}

// ==========================================
// 2. GET ALL REGISTERED PERSONS
// ==========================================
async function loadRegisteredPersons() {
  try {
    const response = await fetch(`${API_BASE_URL}/persons`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const data = await response.json()
    const persons = data.persons
    
    console.log("[v0] Registered persons:", persons)

    // Display persons in UI
    const personsList = document.getElementById("persons-list")
    personsList.innerHTML = persons
      .map(
        (person) => `
      <div class="person-card">
        <h3>${person.name}</h3>
        <p>Status: ${person.status}</p>
        <p>Faces: ${person.face_count || 0}</p>
        <button onclick="deletePerson(${person.person_id})">Delete</button>
      </div>
    `,
      )
      .join("")

    return persons
  } catch (error) {
    console.error("[v0] Error loading persons:", error)
  }
}

// ==========================================
// 3. REGISTER A NEW FACE
// ==========================================
async function registerFace(formElement) {
  try {
    const formData = new FormData(formElement)
    const name = formData.get("name")
    const file = formData.get("file")

    if (!name || !file) {
      alert("Please enter name and select an image")
      return
    }

    console.log("[v0] Registering face for:", name)

    // Convert image to base64
    const reader = new FileReader()
    reader.onload = async (e) => {
      const base64Image = e.target.result.split(",")[1]

      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          image_base64: base64Image,
          status: formData.get("status") || "registered",
          metadata: {}
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to register face")
      }

      const result = await response.json()
      console.log("[v0] Face registered successfully:", result)

      alert(`${name} registered successfully!`)
      formElement.reset()

      // Refresh persons list
      await loadRegisteredPersons()

      return result
    }
    reader.readAsDataURL(file)
  } catch (error) {
    console.error("[v0] Error registering face:", error)
    alert(`Error: ${error.message}`)
  }
}

// ==========================================
// 4. DELETE A PERSON
// ==========================================
async function deletePerson(personId) {
  if (!confirm("Are you sure you want to delete this person?")) return

  try {
    console.log("[v0] Deleting person:", personId)

    const response = await fetch(`${API_BASE_URL}/person/${personId}`, {
      method: "DELETE",
    })

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const result = await response.json()
    console.log("[v0] Person deleted:", result)

    alert("Person deleted successfully")
    await loadRegisteredPersons()
  } catch (error) {
    console.error("[v0] Error deleting person:", error)
    alert("Error deleting person")
  }
}

// ==========================================
// 5. MATCH FACES (Compare with Database)
// ==========================================
async function matchFace(fileInput) {
  try {
    const file = fileInput.files[0]
    if (!file) {
      alert("Please select an image")
      return
    }

    console.log("[v0] Matching face:", file.name)

    // Convert image to base64
    const reader = new FileReader()
    reader.onload = async (e) => {
      const base64Image = e.target.result.split(",")[1]

      const response = await fetch(`${API_BASE_URL}/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: base64Image,
          top_k: 5
        })
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const result = await response.json()
      console.log("[v0] Match result:", result)

      // Display results
      displayMatchResults(result)

      return result
    }
    reader.readAsDataURL(file)
  } catch (error) {
    console.error("[v0] Error matching face:", error)
    alert(`Error: ${error.message}`)
  }
}

// ==========================================
// 6. COMPARE TWO FACES
// ==========================================
async function compareTwoFaces(file1Input, file2Input) {
  try {
    const file1 = file1Input.files[0]
    const file2 = file2Input.files[0]

    if (!file1 || !file2) {
      alert("Please select both images")
      return
    }

    console.log("[v0] Comparing faces")

    // Convert both images to base64
    const reader1 = new FileReader()
    const reader2 = new FileReader()

    let base64_1, base64_2

    reader1.onload = async (e) => {
      base64_1 = e.target.result.split(",")[1]
      
      if (base64_2) {
        const response = await fetch(`${API_BASE_URL}/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image1_base64: base64_1,
            image2_base64: base64_2
          })
        })

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

        const result = await response.json()
        console.log("[v0] Comparison result:", result)
        displayComparisonResult(result)
      }
    }

    reader2.onload = (e) => {
      base64_2 = e.target.result.split(",")[1]
    }

    reader1.readAsDataURL(file1)
    reader2.readAsDataURL(file2)
  } catch (error) {
    console.error("[v0] Error comparing faces:", error)
    alert(`Error: ${error.message}`)
  }
}

// ==========================================
// 7. DISPLAY MATCH RESULTS
// ==========================================
function displayMatchResults(result) {
  const resultsDiv = document.getElementById("match-results") || createResultsDiv()
  
  if (result.num_faces_detected === 0) {
    resultsDiv.innerHTML = "<p>No faces detected in image</p>"
    return
  }

  let html = `<h3>Detected ${result.num_faces_detected} face(s)</h3>`
  
  result.matches.forEach((faceMatch) => {
    html += `<div class="face-match">
      <h4>Face ${faceMatch.face_index + 1}</h4>
      <p>Bounding Box: ${faceMatch.detection_bbox.join(", ")}</p>`
    
    if (faceMatch.matches.length > 0) {
      html += `<h5>Top Matches:</h5><ul>`
      faceMatch.matches.forEach((match, idx) => {
        html += `<li>${idx + 1}. ${match.name} - Distance: ${match.distance.toFixed(3)}, Confidence: ${(match.confidence * 100).toFixed(1)}%</li>`
      })
      html += `</ul>`
    } else {
      html += `<p>No matches found</p>`
    }
    html += `</div>`
  })

  resultsDiv.innerHTML = html
}

// ==========================================
// 8. DISPLAY COMPARISON RESULT
// ==========================================
function displayComparisonResult(result) {
  const resultsDiv = document.getElementById("comparison-results") || createResultsDiv()
  
  const comparison = result.comparison
  resultsDiv.innerHTML = `
    <h3>Face Comparison Result</h3>
    <p><strong>Distance:</strong> ${comparison.distance.toFixed(4)}</p>
    <p><strong>Confidence:</strong> ${(comparison.confidence * 100).toFixed(1)}%</p>
    <p><strong>Match:</strong> ${comparison.match ? "✅ YES" : "❌ NO"}</p>
  `
}

// ==========================================
// 9. HELPER: CREATE RESULTS DIV
// ==========================================
function createResultsDiv() {
  const div = document.createElement("div")
  div.id = "match-results"
  div.className = "results-container"
  document.body.appendChild(div)
  return div
}

// ==========================================
// 10. HEALTH CHECK
// ==========================================
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const data = await response.json()
    console.log("[v0] Backend Health:", data)
    return data
  } catch (error) {
    console.error("[v0] Backend is not running:", error)
    return null
  }
}

// ==========================================
// 11. INITIALIZE DASHBOARD
// ==========================================
async function initializeDashboard() {
  console.log("[v0] Initializing dashboard...")

  try {
    // Check if backend is running
    const health = await checkBackendHealth()
    if (!health) {
      alert("Backend API is not running! Please start the FastAPI server.")
      return
    }

    await loadDashboardStats()
    await loadRegisteredPersons()

    // Refresh stats every 30 seconds
    setInterval(loadDashboardStats, 30000)

    console.log("[v0] Dashboard initialized successfully")
  } catch (error) {
    console.error("[v0] Error initializing dashboard:", error)
  }
}

// ==========================================
// HTML INTEGRATION EXAMPLE
// ==========================================
/*
<html>
  <head>
    <style>
      .dashboard-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px; }
      .stat-card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
      .person-card { border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 8px; }
      .results-container { margin: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px; }
    </style>
  </head>
  <body>
    <!-- Dashboard Stats -->
    <div class="dashboard-stats">
      <div class="stat-card">
        <h3>Registered Persons</h3>
        <p id="total-persons">0</p>
      </div>
      <div class="stat-card">
        <h3>Total Embeddings</h3>
        <p id="total-embeddings">0</p>
      </div>
      <div class="stat-card">
        <h3>Device</h3>
        <p id="device">-</p>
      </div>
      <div class="stat-card">
        <h3>Match Threshold</h3>
        <p id="match-threshold">-</p>
      </div>
    </div>

    <!-- Register Face -->
    <div style="margin: 20px;">
      <h2>Register New Face</h2>
      <form id="register-form" onsubmit="event.preventDefault(); registerFace(this);">
        <input type="text" name="name" placeholder="Person Name" required />
        <select name="status">
          <option value="registered">Registered</option>
          <option value="missing">Missing</option>
          <option value="wanted">Wanted</option>
        </select>
        <input type="file" name="file" accept="image/*" required />
        <button type="submit">Register Face</button>
      </form>
    </div>

    <!-- Match Face -->
    <div style="margin: 20px;">
      <h2>Match Face Against Database</h2>
      <form onsubmit="event.preventDefault(); matchFace(document.getElementById('match-input'));">
        <input type="file" id="match-input" accept="image/*" required />
        <button type="submit">Match Face</button>
      </form>
      <div id="match-results"></div>
    </div>

    <!-- Compare Two Faces -->
    <div style="margin: 20px;">
      <h2>Compare Two Faces</h2>
      <form onsubmit="event.preventDefault(); compareTwoFaces(document.getElementById('compare-1'), document.getElementById('compare-2'));">
        <input type="file" id="compare-1" accept="image/*" required />
        <input type="file" id="compare-2" accept="image/*" required />
        <button type="submit">Compare</button>
      </form>
      <div id="comparison-results"></div>
    </div>

    <!-- Registered Persons -->
    <div style="margin: 20px;">
      <h2>Registered Persons</h2>
      <div id="persons-list"></div>
    </div>

    <script src="frontend-integration-examples.js"></script>
    <script>
      window.addEventListener('load', initializeDashboard);
    </script>
  </body>
</html>
*/