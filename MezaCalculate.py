# 迷宮配件計算
class Meza:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def get_floor(self):
        return self.width * self.height

    def get_wall(self):
        return self.width * self.height + self.width * (self.height - 1) + self.height * (self.width - 1)

    def get_stand(self):
        return (self.width + 1) * (self.height + 1)

    def get_all(self):
        all = [f"floor: {self.get_floor()}", f"wall: {self.get_wall()}", f"stand: {self.get_stand()}"]
        return all


is_continue = 1
while is_continue:
    width = int(input("width: "))
    height = int(input("height: "))
    meza = Meza(width, height)
    print(meza.get_all())
    is_continue = int(input("If you want again, please press 1, else press 0: "))

