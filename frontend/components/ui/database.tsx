"use client"

import type React from "react"
import { useState, useRef } from "react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import {
  Plus,
  Search,
  Filter,
  User,
  AlertTriangle,
  Loader2,
  Trash2,
} from "lucide-react"

import { usePersons } from "@/lib/use-persons"


export default function FaceDatabase() {
  const {
  persons = [],
  loading,
  error,
  addPerson,
  deletePerson,
} = usePersons()

  const [selectedPerson, setSelectedPerson] = useState<any | null>(null)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)

  

  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const [formData, setFormData] = useState({
    name: "",
    age: "",
    case_no: "",
    status: "missing",
  })

  const filteredPersons = persons.filter((p) => {
  const matchesName =
    p.name.toLowerCase().includes(searchTerm.toLowerCase())

  const matchesStatus =
    statusFilter === "all" || p.status === statusFilter

  return matchesName && matchesStatus
})



  const handleAddPerson = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name || !formData.case_no || !selectedFile) {
      alert("Name, case number and image are required")

      return
    }

    try {
      setIsSubmitting(true)
      await addPerson(formData.name, formData.status, selectedFile, formData.case_no, formData.age)
      setIsAddDialogOpen(false)
      setFormData({ name: "", age: "", case_no: "", status: "missing" })
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch {
      alert("Failed to add person")

    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeletePerson = async (id: number) => {
    if (!confirm("Delete this person?")) return
    await deletePerson(id)
  }

  const badgeVariant = (status: string) => {
    if (status === "missing") return "destructive"
    if (status === "wanted") return "default"
    return "secondary"
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Face Database</h1>
          <p className="text-muted-foreground">
            Manage registered persons
          </p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Person
            </Button>
          </DialogTrigger>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Person</DialogTitle>
              <DialogDescription>
                Upload face and details
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleAddPerson} className="space-y-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="Person's name"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Age</Label>
                  <Input
                    type="number"
                    min="0"
                    max="150"
                    value={formData.age}
                    onChange={(e) =>
                      setFormData({ ...formData, age: e.target.value })
                    }
                    placeholder="Age (optional)"
                  />
                </div>
                <div>
                  <Label>Case No. *</Label>
                  <Input
                    value={formData.case_no}
                    onChange={(e) =>
                      setFormData({ ...formData, case_no: e.target.value })
                    }
                    placeholder="Unique case number"
                  />
                </div>
              </div>

              <div>
                <Label>Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(v) =>
                    setFormData({ ...formData, status: v })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="missing">Missing</SelectItem>
                    <SelectItem value="wanted">Wanted</SelectItem>
                    <SelectItem value="found">Found</SelectItem>
                    <SelectItem value="registered">Registered</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) =>
                  setSelectedFile(e.target.files?.[0] || null)
                }
              />

              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Adding..." : "Add Person"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Details Dialog */}
      {selectedPerson && (
        <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{selectedPerson.name}</DialogTitle>
              <DialogDescription>ID: {selectedPerson.id}</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold mb-2">Personal Information</h4>
                <div className="space-y-1 text-sm">
                  <p><strong>Name:</strong> {selectedPerson.name}</p>
                  {selectedPerson.age && <p><strong>Age:</strong> {selectedPerson.age}</p>}
                  <p><strong>Case No.:</strong> {selectedPerson.case_no}</p>
                  <p><strong>Status:</strong> <Badge variant={badgeVariant(selectedPerson.status)}>{selectedPerson.status}</Badge></p>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">System Information</h4>
                <div className="space-y-1 text-sm">
                  <p><strong>Registered:</strong> {new Date(selectedPerson.created_at || Date.now()).toLocaleString()}</p>
                  {selectedPerson.face_image_path && <p><strong>Face Image:</strong> {selectedPerson.face_image_path}</p>}
                  {selectedPerson.embedding_path && <p><strong>Embedding:</strong> {selectedPerson.embedding_path}</p>}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button onClick={() => setIsDetailsOpen(false)}>Close</Button>
              <Button variant="destructive" onClick={() => { handleDeletePerson(selectedPerson.id); setIsDetailsOpen(false) }}>Delete</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Grid */}
      {loading ? (
        <Loader2 className="animate-spin" />
      ) : error ? (
        <AlertTriangle className="text-destructive" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredPersons.map((p) => (
            <Card key={p.id}>
              <CardHeader>
                <CardTitle>{p.name}</CardTitle>
                <CardDescription>Case No. {p.case_no}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1 text-sm">
                  <p><strong>ID:</strong> {p.id}</p>
                  {p.age && <p><strong>Age:</strong> {p.age}</p>}
                  <p><strong>Status:</strong> <Badge variant={badgeVariant(p.status)}>{p.status}</Badge></p>
                </div>

                <div className="flex gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => { setSelectedPerson(p); setIsDetailsOpen(true) }}
                  >
                    View Details
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeletePerson(p.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
