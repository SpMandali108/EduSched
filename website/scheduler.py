import random
import copy

class TimetableScheduler:
    def __init__(self, assignments, slots, rooms, days):
        """
        assignments: List of {subject_id, faculty_id, division, credits, ...}
        slots: List of times e.g. ["09:00", "10:00", ...]
        rooms: List of room IDs
        days: List of days e.g. ["Mon", "Tue", ...]
        """
        self.assignments = assignments
        self.slots = slots
        self.rooms = rooms
        self.days = days
        
        # Flatten assignments based on credits (1 credit = 1 slot per week)
        self.flattened_assignments = []
        for a in self.assignments:
            credits = a.get('credits', 1)
            for _ in range(credits):
                self.flattened_assignments.append(a)

    def create_random_timetable(self):
        timetable = []
        for assignment in self.flattened_assignments:
            gene = {
                "assignment": assignment,
                "day": random.choice(self.days),
                "slot": random.choice(self.slots),
                "room": random.choice(self.rooms)
            }
            timetable.append(gene)
        return timetable

    def fitness(self, timetable):
        """
        Calculates the number of clashes. Lower is better. 0 is perfect.
        """
        clashes = 0
        
        # Track usage
        faculty_usage = {} # (day, slot) -> faculty_id
        division_usage = {} # (day, slot) -> division_id
        room_usage = {} # (day, slot) -> room_id
        
        for gene in timetable:
            day = gene['day']
            slot = gene['slot']
            room = gene['room']
            faculty = gene['assignment']['faculty_id']
            division = gene['assignment']['division']
            
            # 1. Faculty Clash
            if faculty:
                if (day, slot) in faculty_usage and faculty_usage[(day, slot)] == faculty:
                    clashes += 1
                faculty_usage[(day, slot)] = faculty
            
            # 2. Division Clash
            if (day, slot) in division_usage and division_usage[(day, slot)] == division:
                clashes += 1
            division_usage[(day, slot)] = division
            
        # 4. Day Spread Penalty (Workload Management)
        # We want to avoid a faculty having too many classes in one day if they have a lot of credits
        faculty_day_counts = {} # (faculty_id, day) -> count
        for gene in timetable:
            fid = gene['assignment']['faculty_id']
            day = gene['day']
            if fid:
                key = (fid, day)
                faculty_day_counts[key] = faculty_day_counts.get(key, 0) + 1
        
        for (fid, day), count in faculty_day_counts.items():
            if count > 2: # Penalty if more than 2 classes per day for same faculty
                clashes += (count - 2) * 2 

        return clashes

    def crossover(self, parent1, parent2):
        mid = len(parent1) // 2
        child = parent1[:mid] + parent2[mid:]
        return child

    def mutate(self, timetable, mutation_rate=0.1):
        for gene in timetable:
            if random.random() < mutation_rate:
                gene['day'] = random.choice(self.days)
                gene['slot'] = random.choice(self.slots)
                gene['room'] = random.choice(self.rooms)
        return timetable

    def solve(self, population_size=50, generations=100):
        population = [self.create_random_timetable() for _ in range(population_size)]
        
        for gen in range(generations):
            # Sort by fitness (lowest clashes first)
            population.sort(key=lambda x: self.fitness(x))
            
            best_fitness = self.fitness(population[0])
            if best_fitness == 0:
                break
                
            # Selection: Keep top 10%
            new_population = population[:population_size // 10]
            
            # Crossover & Mutation
            while len(new_population) < population_size:
                p1, p2 = random.sample(population[:population_size // 2], 2)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                new_population.append(child)
                
            population = new_population
            
        return population[0] # Return the best one
