import random

class FadeIn:
    def __init__(self, target, start=0, end=255, time=3000):
        self.start_value = start
        self.end_value = end

        self.time = time
        self.elapsed = 0
        self.value = 0
        self.slope = float(self.end_value)/self.time

        self.target = target

    def finished(self):
        return self.elapsed >= self.time

    def animate(self, delta_t):
        self.elapsed += delta_t
        completion = min(self.elapsed, self.time)/float(self.time)
        self.value = self.start_value + self.end_value*completion
        self.target(self.value)

    def skip(self):
        self.elapsed = self.time
        self.value = self.end_value
        self.target(self.value)

class FadeOut:
    def __init__(self, target, start=255, end=0, time=3000):
        self.start_value = start
        self.end_value = end

        self.time = time
        self.elapsed = 0
        self.value = start

        self.target = target

    def finished(self):
        return self.elapsed >= self.time

    def animate(self, delta_t):
        self.elapsed += delta_t
        completion = min(self.elapsed, self.time)/float(self.time)
        self.value = self.start_value - self.start_value*completion
        self.target(self.value)

    def skip(self):
        self.elapsed = self.time
        self.value = self.end_value
        self.target(self.value)

class MoveValue:
    def __init__(self, target, start, end, args=[],  time=200):
        self.start_value = start
        self.end_value = end

        self.time = time
        self.elapsed = 0
        self.value = start
        self.args = args
        self.target = target

    def finished(self):
        return self.elapsed >= self.time

    def animate(self, delta_t):
        self.elapsed += delta_t
        self.value = self.start_value + float(self.end_value - self.start_value)*min(1, float(self.elapsed)/self.time)
        self.target(self.value, *self.args)

    def skip(self):
        self.elapsed = self.time
        self.value = self.end_value
        self.target(self.value, *self.args)

class Delay:
    def __init__(self, time=150):
        self.time = time
        self.elapsed = 0

    def finished(self):
        return self.elapsed >= self.time

    def animate(self, delta_t):
        self.elapsed += delta_t

    def skip(self):
        self.elapsed = self.time

class FrameAnimate:
    def __init__(self, target, frames):
        self.target = target
        self.elapsed = 0
        self.frames = frames
        self.frame  = self.frames[0]
        self.trigger = self.compute_trigger_time( self.frame[1], self.frame[2] )
        self.target(self.frame[0])

    def compute_trigger_time(self, normal, fuzz):
        return normal + random.uniform(0, 1)*fuzz - 1*(random.randint(0,1))

    def animate(self, delta_t):
        self.elapsed += delta_t

        if self.elapsed > self.trigger:
            r = sum(c[1] for c in self.frame[3])
            r = random.uniform(0, r)
            upto = 0
            for choice in self.frame[3]:
                if upto + choice[1] >= r:
                    self.frame = self.frames[choice[0]]
                    self.target(self.frame[0])
                    break
                upto += choice[1]

            self.elapsed = 0
            self.trigger = self.compute_trigger_time(self.frame[1], self.frame[2])

    def reset(self):
        self.elapsed = 0
        self.frame  = self.frames[0]
        self.trigger = self.compute_trigger_time( self.frame[1], self.frame[2] )
        self.target(self.frame[0])

class ChooseRandom:
    def __init__(self, target, options, time=150, fuzz=0):
        self.time = time
        self.fuzz = fuzz
        self.elapsed = 0

        self.target = target
        self.trigger = self.compute_trigger_time(self.time, self.fuzz)
        self.range = sum(c[1] for c in options)
        self.options = options

    def compute_trigger_time(self, normal, fuzz):
        return abs(normal + random.uniform(0, 1)*fuzz - 1*(random.randint(0,1)))

    def animate(self, delta_t):
        self.elapsed += delta_t
        if self.elapsed > self.trigger:
            r = random.uniform(0, self.range)
            upto = 0
            for choice in self.options:
                if upto + choice[1] >= r:
                    self.target(choice[0])
                    break
                upto += choice[1]
            self.elapsed = 0
            self.trigger = self.compute_trigger_time(self.time, self.fuzz)

class MovePosition:
    def __init__(self, start, finish, target, time=150):
        self.start  = start
        self.finish = finish
        self.current = [self.start[0],self.start[1]]
        self.time   = time
        self.target = target
        self.elapsed = 0

    def animate(self, delta_t):
        self.elapsed = min( self.elapsed+delta_t, self.time)
        self.current[0] = self.start[0] + (self.finish[0]-self.start[0]) * min(1, float(self.elapsed)/self.time)
        self.current[1] = self.start[1] + (self.finish[1]-self.start[1]) * min(1, float(self.elapsed)/self.time)
        self.target(self.current)

    def finished(self):
        return self.elapsed >= self.time

    def skip(self):
        self.current = [self.finish[0],self.finish[1]]
        self.elapsed = self.time
        self.target(self.current)

class DelayCallBack:
    def __init__(self, target, args=[], time=150):
        self.time = time
        self.elapsed = 0
        self.args = args
        self.target = target

    def animate(self, delta_t):
        self.elapsed += delta_t
        if self.elapsed >= self.time:
            self.target(*self.args)

    def finished(self):
        return self.elapsed >= self.time

    def skip(self):
        self.elapsed = self.time
        self.target(*self.args)

class Timeout:
    def __init__(self, target, args=[], time=150):
        self.time = time
        self.elapsed = time
        self.args = args
        self.target = target

    def animate(self, delta_t):
        self.elapsed += delta_t
        if self.elapsed >= self.time:
            self.elapsed = 0
            self.target(*self.args)

class ParallelAnimation:
    def __init__(self, animations = None):
        self.animations = animations if animations != None else []

    def animate(self, delta_t):
        for animation in self.animations:
            animation.animate(delta_t)

    def add_animation(self, animation):
        self.animations.append(animation)

    def finished(self):
        for animation in self.animations:
            if not animation.finished():
                return False
        return True

    def skip(self):
        for animation in self.animations:
            if not animation.finished():
                animation.skip()

class SequenceAnimation:
    def __init__(self, animations = None):
        self.animations = animations if animations != None else []
        self.cur_animation = 0

    def animate(self, delta_t):
        if self.cur_animation < len(self.animations):
            self.animations[self.cur_animation].animate(delta_t)
            if self.animations[self.cur_animation].finished():
                self.cur_animation += 1

    def finished(self):
        return self.cur_animation >= len(self.animations)

    def add_animation(self, animation):
        self.animations.append(animation)

    def skip_current(self):
        if self.cur_animation < len(self.animations):
            self.animations[self.cur_animation].skip()
            self.cur_animation += 1

    def skip(self):
        for i in range(self.cur_animation, len(self.animations)):
            self.animations[i].skip()
