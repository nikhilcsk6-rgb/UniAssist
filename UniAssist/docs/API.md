# UniAssist REST API
Base URL `http://localhost:5000/api`. All endpoints except `/health`, `/auth/register`, `/auth/login` need `Authorization: Bearer <token>`. Errors: `{"error": "message"}` with 400/401/403/404/409/413/422/429/502.

| Method & path | Role | Purpose |
|---|---|---|
| GET /health | public | liveness |
| POST /auth/register | public | `{full_name,email,password,role(student\|faculty),department}` |
| POST /auth/login | public | `{email,password}` -> `{access_token,user}` |
| GET/PUT /auth/me | any | profile; PUT `{full_name,preferred_language,theme,current_password,new_password}` |
| GET /admin/users?role= | admin | list users |
| PUT/DELETE /admin/users/{id} | admin | `{is_active,role}` / delete |
| GET /admin/logs | admin | latest 200 audit entries |
| POST /documents | any* | multipart `file,title,category,visibility` (*category permissions: admin=official, faculty=study_material, student=personal) |
| GET /documents?category=&mine=1 | any | own + public documents |
| DELETE /documents/{id} | owner/admin | delete file + vectors |
| POST /documents/{id}/reindex | owner/admin | rebuild embeddings |
| GET /documents/search?q=&top_k= | any | semantic search (respects privacy) |
| GET/POST /chat/sessions | any | list (`?q=` searches) / create `{mode: university\|document\|study, document_id, language, title}` |
| GET/PUT/DELETE /chat/sessions/{id} | owner | messages / rename or language / delete |
| POST /chat/sessions/{id}/messages | owner | `{content}` -> `{user_message, assistant_message{content,sources[{n,filename,page,similarity,snippet}],grounded}}` |
| POST /feedback | any | `{type: rating\|incorrect_report\|suggestion, message_id, rating(1-5), comment}` |
| GET /feedback ; GET /feedback/mine | admin ; any | list |
| POST /assistant/document/{id}/{summary\|key_points\|topics\|notes} | any | `{language}` |
| POST /assistant/explain, /revision-notes, /flashcards | any | `{document_id or topic, level, count, language}` |
| POST /assistant/study-plan | any | `{subject, days, hours_per_day, goals, document_id}` |
| POST /questions/generate | any | `{document_id or topic, title, language, spec:[{type,marks,difficulty,count}]}` |
| GET /questions/papers ; /papers/{pid} ; /papers/{pid}/pdf?answers=1 ; DELETE /papers/{pid} | owner | saved papers |
| POST /quizzes/generate ; GET /quizzes ; GET /quizzes/{id} ; POST /quizzes/{id}/submit ; GET /quizzes/results | any | answers are scored server-side and never sent before submit |
| GET/POST /announcements ; PUT/DELETE /announcements/{id} | read: any; write: faculty/admin | `{title,body,category,audience,event_date}` |
| GET /analytics/me ; GET /analytics/overview | any ; admin | dashboard data |
| POST /research/benchmark | admin | multipart CSV `dataset_name,file` |
| GET /research/datasets ; DELETE /research/datasets/{name} | admin | |
| POST /research/experiments | admin | `{name,dataset_name,top_k,temperature,limit}` runs Model A vs B |
| GET /research/experiments ; /experiments/{id} ; /{id}/export.csv ; /{id}/export.pdf ; DELETE | admin | results/export |
