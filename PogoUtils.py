class PogoUtils:
    def calculate_powerup_cost(self, from_level, to_level):
        COST_PER_POWERUP = {
            1: [200, 1, 0],
            1.5: [200, 1, 0],
            2: [200, 1, 0],
            2.5: [200, 1, 0],
            3: [400, 1, 0],
            3.5: [400, 1, 0],
            4: [400, 1, 0],
            4.5: [400, 1, 0],
            5: [600, 1, 0],
            5.5: [600, 1, 0],
            6: [600, 1, 0],
            6.5: [600, 1, 0],
            7: [800, 1, 0],
            7.5: [800, 1, 0],
            8: [800, 1, 0],
            8.5: [800, 1, 0],
            9: [1000, 1, 0],
            9.5: [1000, 1, 0],
            10: [1000, 1, 0],
            10.5: [1000, 1, 0],
            11: [1300, 2, 0],
            11.5: [1300, 2, 0],
            12: [1300, 2, 0],
            12.5: [1300, 2, 0],
            13: [1600, 2, 0],
            13.5: [1600, 2, 0],
            14: [1600, 2, 0],
            14.5: [1600, 2, 0],
            15: [1900, 2, 0],
            15.5: [1900, 2, 0],
            16: [1900, 2, 0],
            16.5: [1900, 2, 0],
            17: [2200, 2, 0],
            17.5: [2200, 2, 0],
            18: [2200, 2, 0],
            18.5: [2200, 2, 0],
            19: [2500, 2, 0],
            19.5: [2500, 2, 0],
            20: [2500, 2, 0],
            20.5: [2500, 2, 0],
            21: [3000, 3, 0],
            21.5: [3000, 3, 0],
            22: [3000, 3, 0],
            22.5: [3000, 3, 0],
            23: [3500, 3, 0],
            23.5: [3500, 3, 0],
            24: [3500, 3, 0],
            24.5: [3500, 3, 0],
            25: [4000, 3, 0],
            25.5: [4000, 3, 0],
            26: [4000, 4, 0],
            26.5: [4000, 4, 0],
            27: [4500, 4, 0],
            27.5: [4500, 4, 0],
            28: [4500, 4, 0],
            28.5: [4500, 4, 0],
            29: [5000, 4, 0],
            29.5: [5000, 4, 0],
            30: [5000, 4, 0],
            30.5: [5000, 4, 0],
            31: [6000, 6, 0],
            31.5: [6000, 6, 0],
            32: [6000, 6, 0],
            32.5: [6000, 6, 0],
            33: [7000, 8, 0],
            33.5: [7000, 8, 0],
            34: [7000, 8, 0],
            34.5: [7000, 8, 0],
            35: [8000, 10, 0],
            35.5: [0, 0, 0],
            36: [8000, 10, 0],
            36.5: [8000, 10, 0],
            37: [9000, 12, 0],
            37.5: [9000, 12, 0],
            38: [9000, 12, 0],
            38.5: [9000, 12, 0],
            39: [10000, 15, 0],
            39.5: [10000, 15, 0],
            40: [10000, 0, 10],
            40.5: [10000, 0, 10],
            41: [11000, 0, 10],
            41.5: [11000, 0, 10],
            42: [11000, 0, 12],
            42.5: [11000, 0, 12],
            43: [12000, 0, 12],
            43.5: [12000, 0, 12],
            44: [12000, 0, 15],
            44.5: [12000, 0, 15],
            45: [13000, 0, 15],
            45.5: [13000, 0, 15],
            46: [13000, 0, 17],
            46.5: [13000, 0, 17],
            47: [14000, 0, 17],
            47.5: [14000, 0, 17],
            48: [14000, 0, 20],
            48.5: [14000, 0, 20],
            49: [15000, 0, 20],
            49.5: [15000, 0, 20]
        }

        total_stardust = 0
        total_candy = 0
        total_xl_candy = 0

        while from_level < to_level:
            cost = COST_PER_POWERUP[from_level]
            stardust, candy, xl_candy = COST_PER_POWERUP[from_level]
            total_stardust += stardust
            total_candy += candy
            total_xl_candy += xl_candy
            from_level += 0.5
        return {
        'stardust': total_stardust,
        'candy': total_candy,
        'xl_candy': total_xl_candy
        }