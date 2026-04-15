"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { useAppContext } from "lib/contexts/app-context"
import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, Search, Filter, User, Calendar, MapPin, AlertTriangle } from "lucide-react"
import { usePersons } from "@/lib/use-persons"

// Use live persons from backend

export default function FaceDatabase() {
  const router = useRouter()
  const { isLoggedIn, isLoading } = useAppContext()
  const { persons, loading: personsLoading, error: personsError, fetchPersons, addPerson, deletePerson } = usePersons()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [selectedPerson, setSelectedPerson] = useState<any | null>(null)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)
  
  // Add person form state
  const [newPersonName, setNewPersonName] = useState("")
  const [newPersonAge, setNewPersonAge] = useState("")
  const [newPersonStatus, setNewPersonStatus] = useState("")
  const [newPersonCaseNo, setNewPersonCaseNo] = useState("")
  const [newPersonDescription, setNewPersonDescription] = useState("")
  const [newPersonPhoto, setNewPersonPhoto] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      console.log("[v0] User not authenticated, redirecting to login")
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  // Handle adding a new person
  const handleAddPerson = async () => {
    // Validation
    if (!newPersonName.trim()) {
      alert("Please enter a name")
      return
    }
    if (!newPersonStatus) {
      alert("Please select a status")
      return
    }
    if (!newPersonPhoto) {
      alert("Please select a photo to upload")
      return
    }

    setIsSubmitting(true)
    try {
      // For face recognition system, we use the /api/register endpoint
      // Convert image to base64
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const base64Image = (e.target?.result as string).split(',')[1]
          const response = await fetch('http://localhost:8000/api/register', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: newPersonName.trim(),
              image_base64: base64Image,
              status: newPersonStatus || 'registered',
              metadata: {
                case_no: newPersonCaseNo.trim() || `CASE-${Date.now()}`,
                age: newPersonAge ? parseInt(newPersonAge) : null,
                description: newPersonDescription
              }
            })
          })

          if (!response.ok) {
            throw new Error('Failed to register person')
          }

          const result = await response.json()
          if (result.success) {
            // Reset form
            setNewPersonName("")
            setNewPersonAge("")
            setNewPersonStatus("")
            setNewPersonCaseNo("")
            setNewPersonDescription("")
            setNewPersonPhoto(null)

            // Clear file input
            const fileInput = document.getElementById('photo') as HTMLInputElement
            if (fileInput) {
              fileInput.value = ''
            }

            setIsAddDialogOpen(false)

            // Refresh the persons list
            await fetchPersons()

            // Show success message
            alert("Person registered successfully!")
          } else {
            throw new Error(result.message || 'Failed to register person')
          }
        } catch (error) {
          console.error("Error registering person:", error)
          alert("Failed to register person. Please try again.")
        } finally {
          setIsSubmitting(false)
        }
      }
      reader.readAsDataURL(newPersonPhoto)
    } catch (error) {
      console.error("Error adding person:", error)
      alert("Failed to add person. Please try again.")
      setIsSubmitting(false)
    }
  }

  // Handle file selection
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setNewPersonPhoto(file)
    }
  }

  if (isLoading || !isLoggedIn) {
    return null
  }

  if (personsLoading) {
  return <div className="p-6">Loading database...</div>
}

if (personsError) {
  return <div className="p-6 text-red-500">Error loading database</div>
}
  const filteredDatabase = (persons || []).filter((person: any) => {
    const name = (person.name || '').toLowerCase()
    const caseNo = (person.metadata?.case_no || '').toLowerCase()
    const matchesSearch = name.includes(searchTerm.toLowerCase()) || caseNo.includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || (person.status || '').toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "missing":
        return "destructive"
      case "wanted":
        return "default"
      case "found":
        return "secondary"
      default:
        return "secondary"
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex-1 md:ml-64">
        <Header onSearch={() => {}} onExport={() => {}} onDateRangeChange={() => {}} onNotificationClick={() => {}} />

        <main className="p-6 space-y-6">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold">Face Database</h1>
              <p className="text-muted-foreground">Manage registered persons and facial recognition profiles</p>
            </div>

            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Add New Person
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Add New Person</DialogTitle>
                  <DialogDescription>Add a new person to the facial recognition database</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Full Name *</Label>
                    <Input 
                      id="name" 
                      placeholder="Enter full name" 
                      value={newPersonName}
                      onChange={(e) => setNewPersonName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="age">Age</Label>
                    <Input 
                      id="age" 
                      type="number" 
                      placeholder="Enter age (optional)" 
                      value={newPersonAge}
                      onChange={(e) => setNewPersonAge(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="status">Status *</Label>
                    <Select value={newPersonStatus} onValueChange={setNewPersonStatus}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="missing">Missing</SelectItem>
                        <SelectItem value="wanted">Wanted</SelectItem>
                        <SelectItem value="found">Found</SelectItem>
                        <SelectItem value="registered">Registered</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="case-number">Case Number *</Label>
                    <Input 
                      id="case-number" 
                      placeholder="Enter case number" 
                      value={newPersonCaseNo}
                      onChange={(e) => setNewPersonCaseNo(e.target.value)}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea 
                      id="description" 
                      placeholder="Enter description and details (optional)" 
                      value={newPersonDescription}
                      onChange={(e) => setNewPersonDescription(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="photo">Photo Upload *</Label>
                    <Input 
                      id="photo" 
                      type="file" 
                      accept="image/*" 
                      onChange={handleFileChange}
                      required
                    />
                    {newPersonPhoto && (
                      <p className="text-sm text-muted-foreground">
                        Selected: {newPersonPhoto.name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsAddDialogOpen(false)} disabled={isSubmitting}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddPerson} disabled={isSubmitting}>
                    {isSubmitting ? "Adding..." : "Add Person"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Search and Filter */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name or case number..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="missing">Missing</SelectItem>
                      <SelectItem value="wanted">Wanted</SelectItem>
                      <SelectItem value="found">Found</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Database Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Total Persons</p>
                    <p className="text-2xl font-bold">{persons ? persons.length : '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                  <div>
                    <p className="text-sm font-medium">Missing</p>
                    <p className="text-2xl font-bold">{persons ? persons.filter((p:any) => (p.status || '').toLowerCase() === 'missing').length : '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <div>
                    <p className="text-sm font-medium">Wanted</p>
                    <p className="text-2xl font-bold">{persons ? persons.filter((p:any) => (p.status || '').toLowerCase() === 'wanted').length : '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium">Found</p>
                    <p className="text-2xl font-bold">{persons ? persons.filter((p:any) => (p.status || '').toLowerCase() === 'found').length : '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Face Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDatabase.map((person: any) => (
              <Card key={person.person_id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                        <User className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{person.name}</CardTitle>
                        <CardDescription>Registered: {new Date(person.created_at || Date.now()).toLocaleDateString()}</CardDescription>
                      </div>
                    </div>
                    <Badge variant={getStatusColor(person.status)}>{person.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>Registered: {new Date(person.created_at).toLocaleString()}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Case No.: </span>
                    <span className="text-muted-foreground">{person.metadata?.case_no || '—'}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Age: </span>
                    <span className="text-muted-foreground">{person.metadata?.age ? `${person.metadata.age} years` : '—'}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Faces: </span>
                    <span className="text-muted-foreground">{person.face_count || 0}</span>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">{person.metadata?.description || `Status: ${person.status}`}</p>
                  <div className="flex items-center justify-between pt-2">
                    <Button variant="outline" size="sm" onClick={() => { setSelectedPerson(person); setIsDetailsOpen(true) }}>
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredDatabase.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No persons found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || statusFilter !== "all"
                    ? "Try adjusting your search or filter criteria"
                    : "Add your first person to the database to get started"}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Details Dialog */}
          {selectedPerson && (
            <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>{selectedPerson.name}</DialogTitle>
                  <DialogDescription>Detailed information</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">Basic Information</h4>
                    <div className="space-y-2 text-sm">
                      <p><strong>ID:</strong> {selectedPerson.person_id}</p>
                      <p><strong>Name:</strong> {selectedPerson.name}</p>
                      <p><strong>Status:</strong> <Badge variant={getStatusColor(selectedPerson.status)}>{selectedPerson.status}</Badge></p>
                      <p><strong>Registered:</strong> {new Date(selectedPerson.created_at || Date.now()).toLocaleString()}</p>
                      {selectedPerson.metadata?.case_no && <p><strong>Case No:</strong> {selectedPerson.metadata.case_no}</p>}
                      {selectedPerson.metadata?.age && <p><strong>Age:</strong> {selectedPerson.metadata.age} years</p>}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Face Recognition Data</h4>
                    <div className="space-y-2 text-sm">
                      <p><strong>Registered Faces:</strong> {selectedPerson.face_count || 0}</p>
                      {selectedPerson.metadata?.description && <p><strong>Description:</strong> {selectedPerson.metadata.description}</p>}
                    </div>
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-6">
                  <Button variant="outline" onClick={() => setIsDetailsOpen(false)}>Close</Button>
                  <Button variant="destructive" onClick={() => { deletePerson(selectedPerson.id); setIsDetailsOpen(false) }}>Delete Person</Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </main>
      </div>
    </div>
  )
}
