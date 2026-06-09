import httpx
from typing import Optional, List, Dict, Any
from .config import get_settings


class UniversityDataConnector:
    def __init__(self):
        self.settings = get_settings()
        self.use_mock = self.settings.USE_MOCK_DATA
        
    async def _call_api(self, endpoint: str, api_url: str, api_key: str, params: Dict = None) -> Optional[Dict]:
        if self.use_mock or not api_key:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{api_url}{endpoint}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params=params
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None
    
    async def get_student_info(self, student_id: str) -> Optional[Dict]:
        result = await self._call_api(
            f"/students/{student_id}",
            self.settings.UNIV_SIS_API_URL,
            self.settings.UNIV_SIS_API_KEY
        )
        if result:
            return result
        return self._mock_student_info(student_id)
    
    async def get_cgpa(self, student_id: str) -> Optional[float]:
        result = await self._call_api(
            f"/students/{student_id}/cgpa",
            self.settings.UNIV_SIS_API_URL,
            self.settings.UNIV_SIS_API_KEY
        )
        if result and "cgpa" in result:
            return result["cgpa"]
        return self._mock_cgpa(student_id)
    
    async def get_courses(self, student_id: str, semester: str = None) -> List[Dict]:
        params = {"semester": semester} if semester else None
        result = await self._call_api(
            f"/students/{student_id}/courses",
            self.settings.UNIV_SIS_API_URL,
            self.settings.UNIV_SIS_API_KEY,
            params
        )
        if result and "courses" in result:
            return result["courses"]
        return self._mock_courses(student_id)
    
    async def get_attendance(self, student_id: str, course_code: str = None) -> Dict:
        params = {"course": course_code} if course_code else None
        result = await self._call_api(
            f"/students/{student_id}/attendance",
            self.settings.UNIV_SIS_API_URL,
            self.settings.UNIV_SIS_API_KEY,
            params
        )
        if result:
            return result
        return self._mock_attendance(student_id)
    
    async def search_books(self, query: str, limit: int = 10) -> List[Dict]:
        result = await self._call_api(
            "/books/search",
            self.settings.UNIV_LIBRARY_API_URL,
            self.settings.UNIV_LIBRARY_API_KEY,
            {"q": query, "limit": limit}
        )
        if result and "books" in result:
            return result["books"]
        return self._mock_books(query, limit)
    
    async def get_book_availability(self, book_id: str) -> Dict:
        result = await self._call_api(
            f"/books/{book_id}/availability",
            self.settings.UNIV_LIBRARY_API_URL,
            self.settings.UNIV_LIBRARY_API_KEY
        )
        if result:
            return result
        return self._mock_book_availability(book_id)
    
    async def get_shuttle_schedule(self, route: str = None) -> List[Dict]:
        params = {"route": route} if route else None
        result = await self._call_api(
            "/transport/shuttle",
            self.settings.UNIV_TRANSPORT_API_URL,
            self.settings.UNIV_TRANSPORT_API_KEY,
            params
        )
        if result and "schedules" in result:
            return result["schedules"]
        return self._mock_shuttles()
    
    async def get_jobs(self, query: str = None, limit: int = 20) -> List[Dict]:
        params = {"q": query, "limit": limit} if query else {"limit": limit}
        result = await self._call_api(
            "/careers/jobs",
            self.settings.UNIV_HR_API_URL,
            self.settings.UNIV_HR_API_KEY,
            params
        )
        if result and "jobs" in result:
            return result["jobs"]
        return self._mock_jobs(query, limit)
    
    async def get_internships(self, query: str = None) -> List[Dict]:
        params = {"q": query} if query else {}
        result = await self._call_api(
            "/careers/internships",
            self.settings.UNIV_HR_API_URL,
            self.settings.UNIV_HR_API_KEY,
            params
        )
        if result and "internships" in result:
            return result["internships"]
        return self._mock_internships(query)
    
    async def get_class_routine(self, section: str = "64_I", day: str = None) -> Dict:
        from ..automation.routines_data import get_section_routine

        return get_section_routine(section, day)

    async def get_exam_schedule(self, student_id: str, semester: str = None) -> List[Dict]:
        params = {"semester": semester} if semester else None
        result = await self._call_api(
            f"/students/{student_id}/exams",
            self.settings.UNIV_EXAM_API_URL,
            self.settings.UNIV_EXAM_API_KEY,
            params
        )
        if result and "exams" in result:
            return result["exams"]
        return self._mock_exam_schedule(student_id)
    
    def _mock_student_info(self, student_id: str) -> Dict:
        return {
            "student_id": student_id,
            "name": "Mock Student",
            "email": f"{student_id}@diu.edu.bd",
            "department": "CSE",
            "semester": "Spring 2026",
            "enrollment_date": "2023-01-15"
        }
    
    def _mock_cgpa(self, student_id: str) -> float:
        return 3.75
    
    def _mock_courses(self, student_id: str) -> List[Dict]:
        return [
            {"code": "CSE321", "name": "Machine Learning", "credit": 3.0, "grade": "A", "semester": "Spring 2026"},
            {"code": "CSE322", "name": "Computer Networks", "credit": 3.0, "grade": "A-", "semester": "Spring 2026"},
            {"code": "CSE323", "name": "Software Engineering", "credit": 3.0, "grade": "B+", "semester": "Spring 2026"},
            {"code": "CSE324", "name": "Database Systems", "credit": 3.0, "grade": "A", "semester": "Spring 2026"},
        ]
    
    def _mock_attendance(self, student_id: str) -> Dict:
        return {
            "overall": 92.5,
            "courses": {
                "CSE321": 95.0,
                "CSE322": 90.0,
                "CSE323": 88.0,
                "CSE324": 95.0
            }
        }
    
    def _mock_books(self, query: str, limit: int) -> List[Dict]:
        books = [
            {"id": "b001", "title": "Introduction to Algorithms", "author": "Cormen et al.", "isbn": "978-0262033848", "available": 5},
            {"id": "b002", "title": "Clean Code", "author": "Robert C. Martin", "isbn": "978-0132350884", "available": 3},
            {"id": "b003", "title": "Design Patterns", "author": "Gang of Four", "isbn": "978-0201633610", "available": 2},
            {"id": "b004", "title": "Machine Learning Yearning", "author": "Andrew Ng", "isbn": "978-0999245306", "available": 8},
            {"id": "b005", "title": "Deep Learning", "author": "Ian Goodfellow", "isbn": "978-0262035613", "available": 4},
        ]
        if query:
            return [b for b in books if query.lower() in b["title"].lower()][:limit]
        return books[:limit]
    
    def _mock_book_availability(self, book_id: str) -> Dict:
        return {
            "book_id": book_id,
            "available": 3,
            "total": 5,
            "locations": [
                {"shelf": "A-12", "count": 2},
                {"shelf": "B-05", "count": 1}
            ]
        }
    
    def _mock_shuttles(self) -> List[Dict]:
        return [
            {"route": "Mirpur-01", "time": "07:30 AM", "stop": "Mirpur 10", "status": "On Time"},
            {"route": "Mirpur-02", "time": "08:00 AM", "stop": "Mirpur 10", "status": "On Time"},
            {"route": "Uttara", "time": "07:45 AM", "stop": "Uttara Sector 7", "status": "On Time"},
            {"route": "Dhanmondi", "time": "08:15 AM", "stop": "Dhanmondi 27", "status": "Delayed"},
            {"route": "Gulshan", "time": "07:30 AM", "stop": "Gulshan 1", "status": "On Time"},
        ]
    
    def _mock_jobs(self, query: str, limit: int) -> List[Dict]:
        jobs = [
            {"id": "j001", "title": "Software Engineer", "company": "Google", "location": "Remote", "deadline": "2026-06-01", "type": "Full-time"},
            {"id": "j002", "title": "Junior Developer", "company": "TechCorp", "location": "Dhaka", "deadline": "2026-05-20", "type": "Full-time"},
            {"id": "j003", "title": "ML Engineer", "company": "DataAI", "location": "Remote", "deadline": "2026-06-15", "type": "Full-time"},
            {"id": "j004", "title": "Frontend Developer", "company": "WebSolutions", "location": "Dhaka", "deadline": "2026-05-25", "type": "Contract"},
            {"id": "j005", "title": "DevOps Engineer", "company": "CloudTech", "location": "Remote", "deadline": "2026-06-10", "type": "Full-time"},
        ]
        if query:
            return [j for j in jobs if query.lower() in j["title"].lower()][:limit]
        return jobs[:limit]
    
    def _mock_internships(self, query: str) -> List[Dict]:
        internships = [
            {"id": "i001", "title": "Summer Intern - Software", "company": "Microsoft", "duration": "3 months", "stipend": "$2000"},
            {"id": "i002", "title": "Research Intern", "company": "MIT CSAIL", "duration": "6 months", "stipend": "$3000"},
            {"id": "i003", "title": "Frontend Intern", "company": "Shopify", "duration": "4 months", "stipend": "$2500"},
        ]
        if query:
            return [i for i in internships if query.lower() in i["title"].lower()]
        return internships
    
    def _mock_exam_schedule(self, student_id: str) -> List[Dict]:
        return [
            {"course": "CSE321", "title": "Machine Learning", "date": "2026-05-20", "time": "10:00 AM", "room": "A-301"},
            {"course": "CSE322", "title": "Computer Networks", "date": "2026-05-22", "time": "02:00 PM", "room": "B-205"},
            {"course": "CSE323", "title": "Software Engineering", "date": "2026-05-25", "time": "10:00 AM", "room": "A-102"},
            {"course": "CSE324", "title": "Database Systems", "date": "2026-05-27", "time": "02:00 PM", "room": "C-401"},
        ]


university_data = UniversityDataConnector()