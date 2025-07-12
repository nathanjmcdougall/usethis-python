from enum import Enum


class DevelopmentStatusEnum(Enum):
    planning = "planning"
    planning_code = "1"
    prealpha = "prealpha"
    prealpha_code = "2"
    alpha = "alpha"
    alpha_code = "3"
    beta = "beta"
    beta_code = "4"
    production = "production"
    production_code = "5"
    mature = "mature"
    mature_code = "6"
    inactive = "inactive"
    inactive_code = "7"
