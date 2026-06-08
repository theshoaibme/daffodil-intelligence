from app.skills.store import skill_store, global_config_store

def create_movie_picker_skill():
    name = "Mood-Based Movie Picker"
    description = "Suggests movies based on the user's current mood using a curated emotional mapping."
    content = """When a user asks for a movie recommendation based on their mood:
1. Identify the mood (e.g., Happy, Sad, Bored, Stressed, Excited, Angry).
2. Use the following mapping guidelines to suggest genres/themes:
   - Happy: Feel-good, light-hearted comedies, animated movies, or romantic comedies.
   - Sad:
     - To lift mood: Inspirational dramas, heartwarming stories.
     - To lean into it: Poignant dramas, tragic romances.
   - Bored: High-concept sci-fi, gripping thrillers, mystery, or mind-bending plot twists.
   - Stressed/Anxious: Calming nature documentaries, Studio Ghibli films, slow-paced cozy movies.
   - Excited/Energetic: Fast-paced action, high-adrenaline adventure, superhero movies.
   - Angry: High-octane action, sports movies, or cathartic revenge stories.
3. Suggest 3 movies:
   - One 'Safe Bet' (critically acclaimed/popular).
   - One 'Hidden Gem' (lesser known but great).
   - One 'Wild Card' (something unexpected but fitting the mood).
4. For each movie, provide:
   - Title
   - Year
   - Genre
   - A brief sentence on why it fits the current mood.
5. Ask the user if any of these sound appealing or if they want a different 'vibe'.
"""
    
    # Create the skill
    skill = skill_store.create(
        name=name,
        description=description,
        content=content,
        tags=["entertainment", "movies", "mood"]
    )
    print(f"Created skill: {name} with ID: {skill.id}")

    # Add to global config
    config = global_config_store.get()
    if skill.id not in config.skill_ids:
        config.skill_ids.append(skill.id)
        global_config_store.save(config)
        print(f"Added skill {skill.id} to global configuration.")
    else:
        print("Skill already in global configuration.")

if __name__ == "__main__":
    create_movie_picker_skill()
